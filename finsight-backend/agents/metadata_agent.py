# agents/metadata_agent.py
# ─────────────────────────────────────────────────────────────────
# METADATA AGENT — Node 2 in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Extract "about the statement" information — NOT the transactions.
#   This is what shows in the topbar: bank name, account holder, period.
#
# INPUT:  state["raw_text"]  (set by ingestion_agent)
#         state["transactions"] (to find date range)
#         state["bank_format"]  (to use bank-specific regex patterns)
#
# OUTPUT: state["metadata"] → {
#             "bank": "HDFC Bank",
#             "account_holder": "Abhinav Yadav",
#             "account_number": "XXXX1234",  (masked)
#             "period_from": "Jun 2025",
#             "period_to": "Sep 2025",
#             "months": 4,
#             "period_label": "Jun – Sep 2025"
#         }
#
# HOW IT WORKS:
#   Uses regex to find patterns like:
#   "Account Holder: ABHINAV YADAV" or "Name: Abhinav Yadav"
#   "Statement Period: 01/06/2025 to 30/09/2025"
#   Date range is also computed from transactions as fallback.
# ─────────────────────────────────────────────────────────────────

import re
from datetime import datetime


# ── Bank-specific regex patterns ──────────────────────────────────
# Different banks label things differently in their PDF headers.
# We try bank-specific patterns first, then generic fallbacks.

BANK_NAME_PATTERNS = {
    "HDFC": "HDFC Bank Ltd",
    "SBI": "State Bank of India",
    "ICICI": "ICICI Bank Ltd",
    "AXIS": "Axis Bank Ltd",
    "KOTAK": "Kotak Mahindra Bank",
    "PNB": "Punjab National Bank",
    "UNKNOWN": "Unknown Bank",
}

# Regex patterns to extract account holder name from PDF text
# Each pattern tries a different label the bank might use
NAME_PATTERNS = [
    r"(?:Account\s*Holder|Customer\s*Name|Name|A/c\s*Holder)\s*[:\-]\s*([A-Z][A-Za-z\s]{2,50})",
    r"(?:MR\.|MRS\.|MS\.|DR\.)\s+([A-Z][A-Za-z\s]{2,40})",
    r"Dear\s+(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*([A-Z][A-Za-z\s]{2,40}),",
]

# Regex patterns to extract statement period
PERIOD_PATTERNS = [
    r"(?:Statement\s*Period|Period)\s*[:\-]\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|–|-)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    r"(?:From|Start)\s*[:\-]\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}).*?(?:To|End)\s*[:\-]\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    r"(\d{2}/\d{2}/\d{4})\s*(?:to|–|-)\s*(\d{2}/\d{2}/\d{4})",
]

# Regex to find account number (masked for privacy)
ACCOUNT_PATTERNS = [
    r"(?:Account\s*(?:No|Number)|A/c\s*No)\s*[:\-]\s*([X\*\d]{6,20})",
    r"(?:Savings|Current)\s*Account[:\s]+([X\*\d]{6,20})",
]


def extract_account_holder(text: str) -> str:
    """
    Try each name pattern until we find a match.
    Returns "Unknown" if nothing matches.
    """
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Clean up: remove extra whitespace, title case
            name = " ".join(name.split())
            # Sanity check: names shouldn't be too short or too long
            if 3 <= len(name) <= 60:
                return name.title()  # "ABHINAV YADAV" → "Abhinav Yadav"

    return "Unknown"


def extract_account_number(text: str) -> str:
    """
    Extract account number and mask all but last 4 digits for privacy.
    "123456789012" → "XXXX6789012"
    """
    for pattern in ACCOUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            acc_no = match.group(1).strip()
            # Mask everything except last 4
            if len(acc_no) > 4:
                masked = "X" * (len(acc_no) - 4) + acc_no[-4:]
                return masked
            return acc_no

    return "XXXX"


def parse_date_string(date_str: str) -> datetime | None:
    """Parse a date string in various formats, return datetime or None."""
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def get_date_range_from_transactions(transactions: list) -> tuple[datetime | None, datetime | None]:
    """
    Find the earliest and latest dates from the transactions list.
    This is the FALLBACK if we can't find period from PDF header.
    """
    dates = []
    for txn in transactions:
        date_str = txn.get("date", "")
        if date_str:
            dt = parse_date_string(date_str)
            if dt:
                dates.append(dt)

    if not dates:
        return None, None

    return min(dates), max(dates)


def format_period_label(from_dt: datetime, to_dt: datetime) -> dict:
    """
    Given two datetimes, produce the period metadata dict.

    Examples:
        Jun 2025 → Jun 2025  : { "period_label": "Jun 2025", "months": 1 }
        Jun 2025 → Sep 2025  : { "period_label": "Jun – Sep 2025", "months": 4 }
        Jan 2024 → Dec 2024  : { "period_label": "Jan – Dec 2024", "months": 12 }
    """
    # Calculate number of months between dates
    months = (to_dt.year - from_dt.year) * 12 + (to_dt.month - from_dt.month) + 1

    from_label = from_dt.strftime("%b %Y")   # "Jun 2025"
    to_label = to_dt.strftime("%b %Y")       # "Sep 2025"

    if from_label == to_label:
        # Same month
        period_label = from_label
    elif from_dt.year == to_dt.year:
        # Same year, different months: "Jun – Sep 2025"
        period_label = f"{from_dt.strftime('%b')} – {to_label}"
    else:
        # Different years: "Nov 2024 – Jan 2025"
        period_label = f"{from_label} – {to_label}"

    return {
        "period_from": from_label,
        "period_to": to_label,
        "period_label": period_label,
        "months": months,
        "period_from_iso": from_dt.strftime("%Y-%m-%d"),
        "period_to_iso": to_dt.strftime("%Y-%m-%d"),
    }


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────

def metadata_agent(state: dict) -> dict:
    """
    LangGraph node: extract statement metadata from PDF text.

    Input state keys:
        raw_text (str): full PDF text from ingestion_agent
        transactions (list): clean transactions (for date range fallback)
        bank_format (str): bank identifier like "HDFC"

    Output state keys added:
        metadata (dict): bank, account_holder, period info
    """
    print("[MetadataAgent] Starting...")

    raw_text = state.get("raw_text", "")
    transactions = state.get("transactions", [])
    bank_format = state.get("bank_format", "UNKNOWN")

    # ── 1. Bank name ─────────────────────────────────────────────
    bank_name = BANK_NAME_PATTERNS.get(bank_format, "Unknown Bank")
    print(f"[MetadataAgent] Bank: {bank_name}")

    # ── 2. Account holder name ───────────────────────────────────
    account_holder = extract_account_holder(raw_text)
    print(f"[MetadataAgent] Account holder: {account_holder}")

    # ── 3. Account number (masked) ───────────────────────────────
    account_number = extract_account_number(raw_text)

    # ── 4. Date range ────────────────────────────────────────────
    # Try to find it in the PDF header first
    period_from_dt = None
    period_to_dt = None

    for pattern in PERIOD_PATTERNS:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            period_from_dt = parse_date_string(match.group(1))
            period_to_dt = parse_date_string(match.group(2))
            if period_from_dt and period_to_dt:
                print(f"[MetadataAgent] Period found in header")
                break

    # Fallback: derive period from transaction dates
    if not period_from_dt or not period_to_dt:
        print("[MetadataAgent] Period not in header, using transaction dates...")
        period_from_dt, period_to_dt = get_date_range_from_transactions(transactions)

    # ── 5. Build period label ─────────────────────────────────────
    if period_from_dt and period_to_dt:
        period_info = format_period_label(period_from_dt, period_to_dt)
    else:
        period_info = {
            "period_from": "Unknown",
            "period_to": "Unknown",
            "period_label": "Unknown period",
            "months": 0,
        }

    # ── 6. Assemble final metadata dict ──────────────────────────
    metadata = {
        "bank": bank_name,
        "bank_format": bank_format,
        "account_holder": account_holder,
        "account_number": account_number,
        **period_info,
        "total_transactions": len(transactions),
    }

    print(f"[MetadataAgent] ✅ Metadata: {metadata['bank']} · {metadata['account_holder']} · {metadata['period_label']}")

    return {
        **state,
        "metadata": metadata,
    }