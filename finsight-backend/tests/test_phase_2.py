# Test Phase 2
# tests/test_phase2.py
# Run: python tests/test_phase2.py
# For full pipeline: python tests/test_phase2.py tests/sample_statements/hdfc.pdf

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*60)
print("  FinSight AI — Phase 2 Tests")
print("="*60 + "\n")

# ── Test 1: Imports ───────────────────────────────────────────────
print("TEST 1: Checking Phase 2 imports...")
try:
    from services.merchant_db    import lookup_merchant, get_all_categories
    from services.claude_client  import get_client
    from agents.categorization_agent import categorize_single, build_category_summary
    from agents.anomaly_agent    import detect_duplicates, detect_subscription_overlap
    from agents.insight_agent    import add_rule_based_insights
    from agents.aggregator_agent import build_summary
    from agents.pipeline         import build_pipeline
    print("  ✅ All Phase 2 imports successful\n")
except ImportError as e:
    print(f"  ❌ Import failed: {e}\n")
    sys.exit(1)


# ── Test 2: Merchant DB exact match ──────────────────────────────
print("TEST 2: Merchant DB — exact match")
cases = [
    ("Swiggy order payment",       "Food & dining"),
    ("Netflix subscription",        "Entertainment"),
    ("ANI Technologies Pvt Ltd",    "Transport"),
    ("Apollo Pharmacy purchase",    "Health"),
    ("NoBroker rent payment",       "Housing"),
]
for desc, expected_cat in cases:
    result = lookup_merchant(desc)
    got = result["category"] if result else "None"
    status = "✅" if result and result["category"] == expected_cat else "❌"
    print(f"  {status} '{desc[:35]}' → {got} (expected {expected_cat})")
print()


# ── Test 3: Merchant DB pattern match ────────────────────────────
print("TEST 3: Merchant DB — pattern match")
pattern_cases = [
    ("SALARY CREDIT INFOSYS LTD",  "Income"),
    ("ATM CASH WDL BRANCH 1234",   "Banking & transfers"),
    ("NEFT/INFD1234/Rahul Sharma",  "Banking & transfers"),
]
for desc, expected_cat in pattern_cases:
    result = lookup_merchant(desc)
    got = result["category"] if result else "None"
    status = "✅" if result and result["category"] == expected_cat else "❌"
    print(f"  {status} '{desc[:40]}' → {got}")
print()


# ── Test 4: Categorize single transaction ─────────────────────────
print("TEST 4: categorize_single()")
mock_txns = [
    {"description": "Swiggy Technologies", "amount": 648, "type": "debit", "debit": 648, "credit": 0, "date": "2025-06-27", "balance": 0},
    {"description": "Salary Credit",       "amount": 82000, "type": "credit", "debit": 0, "credit": 82000, "date": "2025-06-25", "balance": 0},
    {"description": "UPI/Rahul Sharma",    "amount": 2000, "type": "debit", "debit": 2000, "credit": 0, "date": "2025-06-26", "balance": 0},
]
for txn in mock_txns:
    result = categorize_single(txn)
    print(f"  📝 '{txn['description']}' → {result['category']} [{result['category_source']}] ({result['confidence']:.0%})")
print()


# ── Test 5: Category summary builder ─────────────────────────────
print("TEST 5: build_category_summary()")
mock_categorized = [
    {"type": "debit", "debit": 16430, "category": "Food & dining"},
    {"type": "debit", "debit": 12835, "category": "Housing"},
    {"type": "debit", "debit": 9241,  "category": "Transport"},
    {"type": "credit","credit": 82000,"category": "Income"},
]
summary = build_category_summary(mock_categorized)
for cat in summary:
    print(f"  📊 {cat['category']}: ₹{cat['amount']:,.0f} ({cat['percentage']:.1f}%)")
print()


# ── Test 6: Duplicate detection ───────────────────────────────────
print("TEST 6: detect_duplicates()")
dup_txns = [
    {"type":"debit","description":"Netflix","debit":649,"date":"2025-06-01"},
    {"type":"debit","description":"Netflix","debit":649,"date":"2025-06-02"},  # duplicate!
    {"type":"debit","description":"Swiggy", "debit":200,"date":"2025-06-10"},
]
dupes = detect_duplicates(dup_txns)
print(f"  {'✅' if len(dupes) == 1 else '❌'} Found {len(dupes)} duplicate(s) (expected 1)")
if dupes:
    print(f"     → {dupes[0]['title']}")
print()


# ── Test 7: Subscription overlap ─────────────────────────────────
print("TEST 7: detect_subscription_overlap()")
sub_txns = [
    {"type":"debit","description":"Netflix subscription","debit":649,"date":"2025-06-01"},
    {"type":"debit","description":"Spotify premium",     "debit":119,"date":"2025-06-01"},
    {"type":"debit","description":"Hotstar membership",  "debit":299,"date":"2025-06-01"},
    {"type":"debit","description":"Swiggy order",        "debit":300,"date":"2025-06-10"},
]
overlaps = detect_subscription_overlap(sub_txns)
print(f"  {'✅' if len(overlaps) == 1 else '❌'} Found {len(overlaps)} subscription overlap(s) (expected 1)")
if overlaps:
    print(f"     → {overlaps[0]['title']}")
print()


# ── Test 8: Full pipeline build ───────────────────────────────────
print("TEST 8: build_pipeline() with 6 agents")
try:
    pipeline = build_pipeline()
    print("  ✅ Pipeline compiled: ingestion → metadata → categorization → anomaly → insight → aggregator\n")
except Exception as e:
    print(f"  ❌ Pipeline build failed: {e}\n")


# ── Test 9: Full pipeline on real PDF ────────────────────────────
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
    if os.path.exists(pdf_path):
        print(f"TEST 9: Full pipeline on {pdf_path}")
        from agents.pipeline import run_pipeline
        try:
            result = run_pipeline(file_path=pdf_path, job_id="phase2-test")
            meta    = result.get("metadata", {})
            summary = result.get("summary", {})
            cats    = result.get("categories", [])
            txns    = result.get("transactions", [])
            anomalies = result.get("anomalies", [])
            insights  = result.get("insights", [])

            print(f"\n  ✅ Pipeline complete!")
            print(f"  Bank:          {meta.get('bank')}")
            print(f"  Account:       {meta.get('account_holder')}")
            print(f"  Period:        {meta.get('period_label')}")
            print(f"  Transactions:  {len(txns)}")
            print(f"  Categorized:   {meta.get('categorized_pct')}%")
            print(f"  AI calls made: {meta.get('ai_calls_made')}")
            print(f"  Total income:  ₹{summary.get('total_income',0):,.0f}")
            print(f"  Total spend:   ₹{summary.get('total_spending',0):,.0f}")
            print(f"  Savings rate:  {summary.get('savings_rate',0):.1f}%")
            print(f"\n  Categories:")
            for c in cats:
                print(f"    {c['category']}: ₹{c['amount']:,.0f} ({c['percentage']:.1f}%)")
            print(f"\n  Anomalies ({len(anomalies)}):")
            for a in anomalies:
                print(f"    [{a['severity'].upper()}] {a['title']}")
            print(f"\n  Insights ({len(insights)}):")
            for i in insights:
                print(f"    [{i['type'].upper()}] {i['title']}")
        except Exception as e:
            print(f"  ❌ Pipeline error: {e}")
            import traceback; traceback.print_exc()

print("\n" + "="*60)
print("  Phase 2 tests done!")
print("  To test full pipeline:")
print("  python tests/test_phase2.py tests/sample_statements/your_file.pdf")
print("="*60 + "\n")