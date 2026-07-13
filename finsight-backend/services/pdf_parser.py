# services/pdf_parser.py
# ─────────────────────────────────────────────────────────────────
# RAW PDF PARSING SERVICE
#
# This is NOT an agent — it's a low-level utility service.
# It only knows how to open a PDF and extract text/tables.
# It has NO business logic (no categorization, no analysis).
#
# Think of it like this:
#   pdf_parser  →  gives raw messy data
#   ingestion_agent  →  cleans and structures that data
#
# WHY pdfplumber?
#   Bank PDFs have transaction data in TABLES.
#   pdfplumber is specifically designed to extract tables from PDFs.
#   Regular text extractors (PyPDF2 etc.) break table formatting.
# ─────────────────────────────────────────────────────────────────

import pdfplumber
import pandas as pd
import re
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract ALL raw text from the PDF.
    Used by the metadata agent to find bank name, account holder etc.
    from the header section of the statement.
    """
    full_text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    return full_text


def extract_tables_from_pdf(file_path: str) -> list[dict]:
    """
    Extract transaction rows from PDF tables.
    Returns a list of raw row dicts — NOT yet cleaned or categorized.

    Each dict looks like:
    {
        "raw_date": "27/06/2025",
        "raw_description": "UPI/Swiggy Technologies Pvt Ltd",
        "raw_debit": "648.00",
        "raw_credit": "",
        "raw_balance": "24,350.00"
    }

    WHY "raw_" prefix?
        The ingestion agent will clean these up.
        Keeping them "raw" makes it clear this service hasn't processed them.
    """
    all_rows = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):

            # extract_table() finds the largest table on the page
            # extract_tables() finds ALL tables on the page
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # First row is usually the header
                # e.g. ["Date", "Description", "Debit", "Credit", "Balance"]
                header = table[0]

                # Skip tables that don't look like transaction tables
                # We check if common column names are present
                header_lower = [str(h).lower() if h else "" for h in header]
                is_transaction_table = any(
                    keyword in " ".join(header_lower)
                    for keyword in ["date", "debit", "credit", "narration", "description", "amount"]
                )

                if not is_transaction_table:
                    continue

                # Process remaining rows (skip header row)
                for row in table[1:]:
                    if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                        continue  # skip empty rows

                    row_dict = {
                        "raw_row": row,
                        "header": header,
                        "page": page_num + 1
                    }
                    all_rows.append(row_dict)

    return all_rows


def detect_bank_format(text: str) -> str:
    """
    Detect which bank the statement is from.
    We search the header text for known bank names.

    Returns a bank identifier string like "HDFC", "SBI", "ICICI" etc.
    The ingestion agent uses this to pick the right column mapping.

    WHY is this needed?
        HDFC calls columns: Date | Narration | Value Dt | Debit | Credit | Closing Balance
        SBI calls columns:  Txn Date | Description | Ref No | Debit | Credit | Balance
        Different banks = different column names = need different parsing logic
    """
    text_upper = text.upper()

    bank_patterns = {
        "HDFC": ["HDFC BANK", "HDFC BANK LTD"],
        "SBI": ["STATE BANK OF INDIA", "SBI"],
        "ICICI": ["ICICI BANK", "ICICI BANK LTD"],
        "AXIS": ["AXIS BANK", "AXIS BANK LTD"],
        "KOTAK": ["KOTAK MAHINDRA BANK", "KOTAK BANK"],
        "PNB": ["PUNJAB NATIONAL BANK", "PNB"],
        "BOB": ["BANK OF BARODA", "BOB"],
        "SUVIDHA": ["SUVIDHA NATIONAL BANK", "SUVIDHA"],
    }

    for bank_id, patterns in bank_patterns.items():
        for pattern in patterns:
            if pattern in text_upper:
                return bank_id

    return "UNKNOWN"