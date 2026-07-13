# Test Phase 1
# tests/test_phase1.py
# ─────────────────────────────────────────────────────────────────
# PHASE 1 TEST SCRIPT
#
# Run this to verify everything works BEFORE connecting the frontend.
# Tests each piece independently so you know exactly where issues are.
#
# HOW TO RUN:
#   cd finsight-backend
#   python tests/test_phase1.py
#
# WHAT IT TESTS:
#   1. pdf_parser    → can we open a PDF and extract text/tables?
#   2. ingestion     → do raw rows become clean transactions?
#   3. metadata      → is bank/name/period extracted correctly?
#   4. pipeline      → does the full LangGraph flow run end to end?
#   5. API schema    → do our Pydantic models validate correctly?
# ─────────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*60)
print("  FinSight AI — Phase 1 Tests")
print("="*60 + "\n")

# ── Test 1: Imports ───────────────────────────────────────────────
print("TEST 1: Checking imports...")
try:
    from services.pdf_parser import extract_text_from_pdf, detect_bank_format
    from agents.ingestion_agent import clean_amount, clean_date, clean_description
    from agents.metadata_agent import extract_account_holder, format_period_label
    from agents.pipeline import build_pipeline, run_pipeline
    from api.schemas import AnalyzeResponse, Transaction, StatementMetadata
    print("  ✅ All imports successful\n")
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    print("  → Run: pip install -r requirements.txt\n")
    sys.exit(1)


# ── Test 2: Amount cleaning ───────────────────────────────────────
print("TEST 2: clean_amount()")
test_amounts = [
    ("1,24,350.00", 124350.0),
    ("₹ 648.00",    648.0),
    ("648.00 Dr",   648.0),
    ("",            0.0),
    (None,          0.0),
    ("12,500",      12500.0),
]
for raw, expected in test_amounts:
    result = clean_amount(raw)
    status = "✅" if result == expected else "❌"
    print(f"  {status} clean_amount({repr(raw)!r}) = {result} (expected {expected})")
print()


# ── Test 3: Date cleaning ─────────────────────────────────────────
print("TEST 3: clean_date()")
test_dates = [
    ("27/06/2025",  "2025-06-27"),
    ("27-Jun-2025", "2025-06-27"),
    ("27 Jun 2025", "2025-06-27"),
    ("",            ""),
]
for raw, expected in test_dates:
    result = clean_date(raw)
    status = "✅" if result == expected else "❌"
    print(f"  {status} clean_date({repr(raw)}) = {repr(result)} (expected {repr(expected)})")
print()


# ── Test 4: Description cleaning ─────────────────────────────────
print("TEST 4: clean_description()")
test_descs = [
    "UPI/Swiggy Technologies Pvt Ltd/9876543210/HDFC0001234",
    "NEFT/INFD21234567890/Rahul Sharma/SBI0012345",
    "ATM-CASH WDL 1234",
    "Netflix Entertainment",
]
for raw in test_descs:
    result = clean_description(raw)
    print(f"  📝 {repr(raw)}\n     → {repr(result)}")
print()


# ── Test 5: Bank detection ────────────────────────────────────────
print("TEST 5: detect_bank_format()")
test_texts = [
    ("HDFC BANK LTD Account Statement", "HDFC"),
    ("State Bank of India - Account Statement", "SBI"),
    ("ICICI BANK LIMITED", "ICICI"),
    ("Some random text with no bank", "UNKNOWN"),
]
for text, expected in test_texts:
    result = detect_bank_format(text)
    status = "✅" if result == expected else "❌"
    print(f"  {status} detect_bank_format({repr(text[:30])+'...'!r}) = {result}")
print()


# ── Test 6: Period formatting ─────────────────────────────────────
print("TEST 6: format_period_label()")
from datetime import datetime
test_periods = [
    (datetime(2025, 6, 1),  datetime(2025, 6, 30),  "Jun 2025",        1),
    (datetime(2025, 6, 1),  datetime(2025, 9, 30),  "Jun – Sep 2025",  4),
    (datetime(2024, 1, 1),  datetime(2024, 12, 31), "Jan – Dec 2024",  12),
    (datetime(2024, 11, 1), datetime(2025, 1, 31),  "Nov 2024 – Jan 2025", 3),
]
for from_dt, to_dt, expected_label, expected_months in test_periods:
    result = format_period_label(from_dt, to_dt)
    label_ok = result["period_label"] == expected_label
    months_ok = result["months"] == expected_months
    status = "✅" if (label_ok and months_ok) else "❌"
    print(f"  {status} {from_dt.strftime('%b %Y')} → {to_dt.strftime('%b %Y')} = {result['period_label']} ({result['months']} months)")
print()


# ── Test 7: LangGraph pipeline build ─────────────────────────────
print("TEST 7: build_pipeline()")
try:
    pipeline = build_pipeline()
    print(f"  ✅ Pipeline built successfully")
    print(f"  ℹ  Nodes: ingestion → metadata → aggregator → END\n")
except Exception as e:
    print(f"  ❌ Pipeline build failed: {e}\n")


# ── Test 8: Pipeline with mock data ──────────────────────────────
print("TEST 8: run_pipeline() with mock PDF")
print("  (Skipped — place a real PDF in tests/sample_statements/)")
print("  To test: python tests/test_phase1.py tests/sample_statements/hdfc.pdf\n")

# If a PDF path is passed as argument, run the full pipeline
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
    if os.path.exists(pdf_path):
        print(f"  Running pipeline on: {pdf_path}")
        try:
            result = run_pipeline(file_path=pdf_path, job_id="test-001")
            meta = result.get("metadata", {})
            txns = result.get("transactions", [])
            summary = result.get("summary", {})
            print(f"  ✅ Pipeline complete!")
            print(f"     Bank:         {meta.get('bank')}")
            print(f"     Account:      {meta.get('account_holder')}")
            print(f"     Period:       {meta.get('period_label')}")
            print(f"     Transactions: {len(txns)}")
            print(f"     Total spent:  ₹{summary.get('total_spending', 0):,.2f}")
            print(f"     Total income: ₹{summary.get('total_income', 0):,.2f}")
        except Exception as e:
            print(f"  ❌ Pipeline failed: {e}")
    else:
        print(f"  ❌ File not found: {pdf_path}")


# ── Test 9: Pydantic schema validation ───────────────────────────
print("\nTEST 9: Pydantic schema validation")
try:
    txn = Transaction(
        date="2025-06-27",
        description="Swiggy Technologies",
        debit=648.0,
        credit=0.0,
        balance=24350.0,
        type="debit",
        amount=648.0,
    )
    print(f"  ✅ Transaction schema valid: {txn.description} — ₹{txn.amount}")
except Exception as e:
    print(f"  ❌ Schema validation failed: {e}")
print()


print("="*60)
print("  All tests done!")
print("  Next step: place an HDFC/SBI PDF in tests/sample_statements/")
print("  Then run: python tests/test_phase1.py tests/sample_statements/your_file.pdf")
print("="*60 + "\n")