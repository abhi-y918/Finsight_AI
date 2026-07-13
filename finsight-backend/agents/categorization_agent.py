# agents/categorization_agent.py
# ─────────────────────────────────────────────────────────────────
# CATEGORIZATION AGENT — Node 3 in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Assign a spending category to every transaction.
#
# THE 3-LAYER STRATEGY (cheapest to most expensive):
#
#   1. Merchant DB (free, instant)
#      "Swiggy" → exact match → "Food & dining" ✅
#
#   2. Fuzzy match (free, instant)
#      "Swiggy Technologies Pvt Ltd" → 92% match → "Food & dining" ✅
#
#   3. Pattern match (free, instant)
#      "UPI/Rahul Sharma" → regex → "Banking & transfers" ✅
#
#   4. Claude API (costs tokens, ~1 second)
#      "MISC/XYZ Corp/123" → no match found → ask Claude ❓
#
# WHY THIS ORDER?
#   A typical 84-transaction statement has ~70 known merchants.
#   Calling Claude for all 84 = expensive + slow.
#   Calling Claude for only 14 unknowns = cheap + fast.
#
# INPUT:  state["transactions"]         (list of clean txn dicts)
# OUTPUT: state["categorized_transactions"] (same list + category fields)
#         state["category_summary"]     (spend per category)
#         state["categorization_stats"] (how many DB vs AI matches)
# ─────────────────────────────────────────────────────────────────

from services.merchant_db import lookup_merchant
from services.claude_client import categorize_transaction


def categorize_single(txn: dict) -> dict:
    """
    Categorize one transaction using the 3-layer strategy.

    Args:
        txn: a clean transaction dict from ingestion_agent

    Returns:
        The same dict with category, category_source, confidence added
    """
    description = txn.get("description", "")
    amount = txn.get("amount", 0)
    txn_type = txn.get("type", "debit")

    # ── Special case: income transactions ────────────────────────
    # Credit transactions that aren't known services = income
    # We handle this before DB lookup to avoid mislabeling salary
    if txn_type == "credit":
        # Check merchant DB first (some credits ARE known: cashback, refunds)
        db_result = lookup_merchant(description)
        if db_result:
            return {
                **txn,
                "category": db_result["category"],
                "category_source": db_result["source"],
                "confidence": db_result["confidence"],
            }
        # Unknown credit → likely salary or transfer
        return {
            **txn,
            "category": "Income",
            "category_source": "pattern_match",
            "confidence": 0.85,
        }

    # ── Layer 1, 2, 3: Merchant DB + fuzzy + pattern ─────────────
    db_result = lookup_merchant(description)
    if db_result:
        return {
            **txn,
            "category": db_result["category"],
            "category_source": db_result["source"],
            "confidence": db_result["confidence"],
        }

    # ── Layer 4: Claude API ───────────────────────────────────────
    # Only reaches here if all DB/pattern lookups failed
    print(f"[CategorizationAgent] Sending to Claude: '{description}'")

    claude_result = categorize_transaction(
        description=description,
        amount=amount,
        txn_type=txn_type,
    )

    if claude_result and "category" in claude_result:
        return {
            **txn,
            "category": claude_result.get("category", "Others"),
            "category_source": "ai_match",
            "confidence": claude_result.get("confidence", 0.7),
            "ai_reasoning": claude_result.get("reasoning", ""),
        }

    # All layers failed → Others + flag for review
    print(f"[CategorizationAgent] ⚠ Could not categorize: '{description}'")
    return {
        **txn,
        "category": "Others",
        "category_source": "review",   # frontend shows "Review" badge
        "confidence": 0.0,
    }


def build_category_summary(categorized_txns: list) -> list:
    """
    Aggregate transactions into per-category totals for the dashboard.

    Returns a list sorted by amount descending — ready for the donut chart.

    Example output:
    [
        { "category": "Food & dining", "amount": 16430, "count": 24, "percentage": 32.0 },
        { "category": "Housing",       "amount": 12835, "count":  3, "percentage": 25.0 },
        ...
    ]
    """
    # Group debit transactions by category
    # (we don't include income/credits in spending breakdown)
    category_totals: dict[str, dict] = {}

    total_spending = 0.0

    for txn in categorized_txns:
        if txn.get("type") != "debit":
            continue

        category = txn.get("category", "Others")
        amount = txn.get("debit", 0)
        total_spending += amount

        if category not in category_totals:
            category_totals[category] = {"amount": 0.0, "count": 0}

        category_totals[category]["amount"] += amount
        category_totals[category]["count"] += 1

    # Build sorted list with percentages
    summary = []
    for category, data in category_totals.items():
        percentage = (data["amount"] / total_spending * 100) if total_spending > 0 else 0
        summary.append({
            "category": category,
            "amount": round(data["amount"], 2),
            "count": data["count"],
            "percentage": round(percentage, 1),
        })

    # Sort by amount descending (biggest spender first)
    summary.sort(key=lambda x: x["amount"], reverse=True)
    return summary


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────

def categorization_agent(state: dict) -> dict:
    """
    LangGraph node: categorize all transactions.

    Input state keys:
        transactions (list): clean transactions from ingestion_agent

    Output state keys added:
        categorized_transactions (list): transactions with category added
        category_summary (list):         per-category spend totals
        categorization_stats (dict):     how many were DB vs AI matched
    """
    print("[CategorizationAgent] Starting...")

    transactions = state.get("transactions", [])

    if not transactions:
        print("[CategorizationAgent] ⚠ No transactions to categorize")
        return {
            **state,
            "categorized_transactions": [],
            "category_summary": [],
            "categorization_stats": {},
        }

    # Categorize each transaction
    categorized = []
    stats = {"exact_match": 0, "fuzzy_match": 0, "pattern_match": 0, "ai_match": 0, "review": 0}

    for i, txn in enumerate(transactions):
        print(f"[CategorizationAgent] {i+1}/{len(transactions)}: {txn.get('description', '')[:40]}")
        result = categorize_single(txn)
        categorized.append(result)

        # Track stats
        source = result.get("category_source", "review")
        if source in stats:
            stats[source] += 1

    # Build category summary for donut chart
    category_summary = build_category_summary(categorized)

    # How many were categorized without AI (free)?
    free_count = stats["exact_match"] + stats["fuzzy_match"] + stats["pattern_match"]
    ai_count = stats["ai_match"]
    total = len(categorized)
    categorized_pct = round((total - stats["review"]) / total * 100) if total > 0 else 0

    print(f"[CategorizationAgent] ✅ Done — {free_count} DB matches, {ai_count} AI matches, {stats['review']} for review")
    print(f"[CategorizationAgent] Categorization rate: {categorized_pct}%")

    return {
        **state,
        "categorized_transactions": categorized,
        "category_summary": category_summary,
        "categorization_stats": {
            **stats,
            "total": total,
            "categorized_pct": categorized_pct,
            "ai_calls_made": ai_count,
        },
    }