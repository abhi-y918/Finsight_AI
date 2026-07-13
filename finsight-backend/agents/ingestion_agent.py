# agents/ingestion_agent.py
# ─────────────────────────────────────────────────────────────────
# INGESTION AGENT — Node 1 in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Take the raw PDF rows from pdf_parser and turn them into
#   clean, structured transaction objects.
#
# WHAT IT DOES:
#   1. Calls pdf_parser to get raw rows
#   2. Detects the bank format (HDFC, SBI etc.)
#   3. Maps the right columns based on bank format
#   4. Cleans dates, amounts, descriptions
#   5. Returns a list of clean Transaction dicts
#
# WHAT IT DOES NOT DO:
#   - No categorization (that's categorization_agent)
#   - No analysis (that's anomaly_agent)
#   - No metadata extraction (that's metadata_agent)
#
# HOW LANGGRAPH WORKS:
#   LangGraph passes a shared "state" dict between agents.
#   Each agent READS from state and WRITES back to state.
#   This agent reads:  state["file_path"]
#   This agent writes: state["transactions"], state["bank_format"], state["raw_text"]
# ─────────────────────────────────────────────────────────────────

import re
from datetime import datetime
from services.pdf_parser import extract_text_from_pdf, extract_tables_from_pdf, detect_bank_format


# ── Bank column mappings ──────────────────────────────────────────
# Different banks use different column names for the same data.
# This dict tells us which column index maps to which field.
#
# Format: { "BANK_ID": { "date": col_index, "description": col_index, ... } }
# col_index is the position of that column in the table row (0-based)

BANK_COLUMN_MAPS = {
    "HDFC": {
        # Date | Narration | Value Dt | Debit Amt | Credit Amt | Chq/Ref | Closing Balance
        "date": 0,
        "description": 1,
        "debit": 3,
        "credit": 4,
        "balance": 6,
    },
    "SBI": {
        # Txn Date | Value Date | Description | Ref No./Cheque No. | Debit | Credit | Balance
        "date": 0,
        "description": 2,
        "debit": 4,
        "credit": 5,
        "balance": 6,
    },
    "ICICI": {
        # Transaction Date | Value Date | S No. | Transaction Remarks | Withdrawal Amt (INR) | Deposit Amt (INR) | Balance (INR)
        "date": 0,
        "description": 3,
        "debit": 4,
        "credit": 5,
        "balance": 6,
    },
    "AXIS": {
        # Tran Date | PARTICULARS | Dr/Cr | Tran Amount | Balance
        "date": 0,
        "description": 1,
        "debit_credit_flag": 2,  # "Dr" or "Cr"
        "amount": 3,             # single amount column
        "balance": 4,
    },
    "SUVIDHA": {
        # Date | Description | Category | Debit (Rs.) | Credit (Rs.) | Balance (Rs.)
        "date": 0,
        "description": 1,
        "debit": 3,
        "credit": 4,
        "balance": 5,
    },
    # Fallback: try to auto-detect columns by header names
    "UNKNOWN": {
        "date": 0,
        "description": 1,
        "debit": 2,
        "credit": 3,
        "balance": 4,
    },
}


def clean_amount(value: str) -> float:
    """
    Convert messy amount strings to clean floats.

    Examples:
        "1,24,350.00" → 124350.0   (Indian number formatting)
        "₹ 648.00"    → 648.0
        "648.00 Dr"   → 648.0
        ""            → 0.0
        None          → 0.0
    """
    if not value:
        return 0.0

    # Remove currency symbols, commas, spaces, Dr/Cr labels
    cleaned = str(value)
    cleaned = re.sub(r'[₹,\s]', '', cleaned)
    cleaned = re.sub(r'(Dr|Cr|DR|CR)$', '', cleaned).strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean_date(value: str) -> str:
    """
    Parse various date formats banks use and return ISO format.

    Examples:
        "27/06/2025"  → "2025-06-27"
        "27-Jun-2025" → "2025-06-27"
        "27 Jun 2025" → "2025-06-27"
        "20250627"    → "2025-06-27"
    """
    if not value:
        return ""

    value = str(value).strip()

    # Try multiple formats
    formats = [
        "%d/%m/%Y",    # 27/06/2025
        "%d-%m-%Y",    # 27-06-2025
        "%d-%b-%Y",    # 27-Jun-2025
        "%d %b %Y",    # 27 Jun 2025
        "%Y%m%d",      # 20250627
        "%d/%m/%y",    # 27/06/25
        "%m/%d/%Y",    # 06/27/2025 (some banks use US format)
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")  # always output ISO format
        except ValueError:
            continue

    # If nothing worked, return as-is
    return value


def clean_description(value: str) -> str:
    """
    Clean up the messy transaction description strings banks produce.

    Examples:
        "UPI/Swiggy Technologies Pvt Ltd/9876543210/HDFC0001234"
            → "UPI / Swiggy Technologies Pvt Ltd"

        "NEFT/INFD21234567890/Rahul Sharma/SBI0012345"
            → "NEFT / Rahul Sharma"

        "ATM-CASH WDL/BRANCH HDFC 1234"
            → "ATM Cash Withdrawal"
    """
    if not value:
        return ""

    desc = str(value).strip()

    # Remove reference numbers (long digit strings after /)
    desc = re.sub(r'/\d{10,}', '', desc)

    # Remove IFSC codes (format: 4 letters + 7 alphanumeric)
    desc = re.sub(r'/[A-Z]{4}[0-9A-Z]{7}', '', desc)

    # Remove account numbers (8-16 digit strings)
    desc = re.sub(r'\b\d{8,16}\b', '', desc)

    # Normalize slashes and spaces
    desc = re.sub(r'\s*/\s*', ' / ', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()

    # Remove trailing slashes
    desc = desc.rstrip('/ ').strip()

    return desc


def map_row_to_transaction(row: list, col_map: dict, bank: str) -> dict | None:
    """
    Take a raw table row and col_map and produce a clean transaction dict.

    Returns None if the row doesn't look like a valid transaction
    (e.g. subtotal rows, header rows repeated mid-table, empty rows).
    """
    try:
        # Get values safely (row might be shorter than expected)
        def get(index):
            if index < len(row):
                return row[index]
            return None

        raw_date = get(col_map.get("date", 0))
        raw_desc = get(col_map.get("description", 1))

        # AXIS bank has a single amount column with Dr/Cr flag
        if bank == "AXIS":
            raw_amount = get(col_map.get("amount", 3))
            dr_cr = str(get(col_map.get("debit_credit_flag", 2)) or "").upper()
            amount = clean_amount(raw_amount)
            debit = amount if "DR" in dr_cr else 0.0
            credit = amount if "CR" in dr_cr else 0.0
        else:
            debit = clean_amount(get(col_map.get("debit", 2)))
            credit = clean_amount(get(col_map.get("credit", 3)))

        balance = clean_amount(get(col_map.get("balance", -1)))
        date = clean_date(raw_date)
        description = clean_description(raw_desc)

        # Skip rows that don't have a valid date or description
        if not date or not description:
            return None

        # Skip rows that look like totals or summaries
        skip_keywords = ["total", "opening balance", "closing balance", "brought forward"]
        if any(kw in description.lower() for kw in skip_keywords):
            return None

        # Determine transaction type
        if credit > 0 and debit == 0:
            txn_type = "credit"
        elif debit > 0 and credit == 0:
            txn_type = "debit"
        else:
            txn_type = "unknown"

        return {
            "date": date,
            "description": description,
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "type": txn_type,
            "amount": debit if txn_type == "debit" else credit,
            # These will be filled in by later agents:
            "category": None,
            "category_source": None,   # "db_match", "ai_match", "review"
            "confidence": None,
        }

    except Exception as e:
        # Don't crash the whole pipeline on one bad row
        print(f"[IngestionAgent] Skipping row due to error: {e}")
        return None


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────
# This is what LangGraph calls as a "node" in the pipeline.
# It receives the full state dict and returns updated state.

def ingestion_agent(state: dict) -> dict:
    """
    LangGraph node: parse PDF and extract clean transactions.

    Input state keys:
        file_path (str): path to the uploaded PDF

    Output state keys added:
        raw_text (str): full text of the PDF (for metadata agent)
        bank_format (str): detected bank e.g. "HDFC"
        transactions (list[dict]): clean transaction objects
        ingestion_error (str|None): error message if something went wrong
    """
    print("[IngestionAgent] Starting...")

    file_path = state.get("file_path")
    if not file_path:
        return {**state, "ingestion_error": "No file_path in state"}

    try:
        # Step 1: Extract raw text (used by metadata agent next)
        print("[IngestionAgent] Extracting raw text...")
        raw_text = extract_text_from_pdf(file_path)

        # Step 2: Detect which bank this statement is from
        bank_format = detect_bank_format(raw_text)
        print(f"[IngestionAgent] Detected bank: {bank_format}")

        # Step 3: Get column mapping for this bank
        col_map = BANK_COLUMN_MAPS.get(bank_format, BANK_COLUMN_MAPS["UNKNOWN"])

        # Step 4: Extract raw table rows from PDF
        print("[IngestionAgent] Extracting tables...")
        raw_rows = extract_tables_from_pdf(file_path)
        print(f"[IngestionAgent] Found {len(raw_rows)} raw rows")

        # Step 5: Map each raw row → clean transaction dict
        transactions = []
        for row_data in raw_rows:
            txn = map_row_to_transaction(
                row=row_data["raw_row"],
                col_map=col_map,
                bank=bank_format
            )
            if txn:
                transactions.append(txn)

        print(f"[IngestionAgent] ✅ Extracted {len(transactions)} valid transactions")

        return {
            **state,
            "raw_text": raw_text,
            "bank_format": bank_format,
            "transactions": transactions,
            "ingestion_error": None,
        }

    except Exception as e:
        print(f"[IngestionAgent] ❌ Error: {e}")
        return {
            **state,
            "ingestion_error": str(e),
            "transactions": [],
        }