# agents/aggregator_agent.py
# ─────────────────────────────────────────────────────────────────
# AGGREGATOR AGENT — Node 6 (Final) in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Collect everything all previous agents produced and
#   assemble ONE clean JSON object for the frontend.
#
# WHY A SEPARATE AGENT?
#   Separation of concerns — each agent does one thing.
#   The aggregator knows the final JSON shape.
#   If we want to change the API response structure,
#   we only touch this file — no other agent changes.
#
# WHAT IT PRODUCES:
#   {
#     "metadata":     { bank, account_holder, period... }
#     "summary":      { income, spending, savings, rate }
#     "categories":   [ { category, amount, percentage }... ]
#     "transactions": [ { date, desc, amount, category }... ]
#     "anomalies":    [ { type, title, description }... ]
#     "insights":     [ { title, description, type }... ]
#     "stats":        { categorization stats }
#   }
# ─────────────────────────────────────────────────────────────────


def build_summary(transactions: list, metadata: dict) -> dict:
    """
    Build the top-level financial summary (the 4 metric cards).
    """
    months = metadata.get("months", 1)

    total_income   = sum(t.get("credit", 0) for t in transactions if t.get("type") == "credit")
    total_spending = sum(t.get("debit", 0)  for t in transactions if t.get("type") == "debit")
    net = total_income - total_spending
    savings_rate = (net / total_income * 100) if total_income > 0 else 0

    return {
        "total_income":        round(total_income, 2),
        "total_spending":      round(total_spending, 2),
        "net":                 round(net, 2),
        "savings":             round(net, 2),
        "savings_rate":        round(savings_rate, 1),
        "monthly_avg_spend":   round(total_spending / months, 2) if months > 0 else total_spending,
        "monthly_avg_income":  round(total_income / months, 2)   if months > 0 else total_income,
        "total_transactions":  len(transactions),
    }


def clean_transactions_for_response(transactions: list) -> list:
    """
    Strip internal fields before sending to frontend.
    Frontend doesn't need raw_row, page number etc.
    Also sort by date descending (newest first).
    """
    cleaned = []
    for txn in transactions:
        cleaned.append({
            "date":             txn.get("date", ""),
            "description":      txn.get("description", ""),
            "debit":            txn.get("debit", 0),
            "credit":           txn.get("credit", 0),
            "balance":          txn.get("balance", 0),
            "amount":           txn.get("amount", 0),
            "type":             txn.get("type", ""),
            "category":         txn.get("category", "Others"),
            "category_source":  txn.get("category_source", "review"),
            "confidence":       txn.get("confidence", 0),
        })

    # Sort newest first
    cleaned.sort(key=lambda x: x.get("date", ""), reverse=True)
    return cleaned


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────

def aggregator_agent(state: dict) -> dict:
    """
    LangGraph node: assemble the final dashboard JSON.

    Reads everything from state and produces state["result"].
    This is what GET /result/{job_id} returns to the frontend.
    """
    print("[AggregatorAgent] Assembling final result...")

    metadata    = state.get("metadata", {})
    transactions = state.get("categorized_transactions") or state.get("transactions", [])
    categories  = state.get("category_summary", [])
    anomalies   = state.get("anomalies", [])
    insights    = state.get("insights", [])
    cat_stats   = state.get("categorization_stats", {})

    # Build summary
    summary = build_summary(transactions, metadata)

    # Add categorization rate to metadata (for the "97% categorized" card)
    metadata["categorized_pct"] = cat_stats.get("categorized_pct", 0)
    metadata["ai_calls_made"]   = cat_stats.get("ai_calls_made", 0)

    # Clean transactions for response
    clean_txns = clean_transactions_for_response(transactions)

    # Final result object
    result = {
        "metadata":     metadata,
        "summary":      summary,
        "categories":   categories,
        "transactions": clean_txns,
        "anomalies":    anomalies,
        "insights":     insights,
        "stats": {
            "categorization": cat_stats,
            "total_anomalies": len(anomalies),
            "total_insights":  len(insights),
        },
        "phase": 2,
    }

    total_spend = summary.get("total_spending", 0)
    print(f"[AggregatorAgent] ✅ Result assembled:")
    print(f"  Transactions : {len(clean_txns)}")
    print(f"  Categories   : {len(categories)}")
    print(f"  Anomalies    : {len(anomalies)}")
    print(f"  Insights     : {len(insights)}")
    print(f"  Total spend  : ₹{total_spend:,.0f}")

    return {
        **state,
        "result": result,
        "current_step": "complete",
        "completed_steps": state.get("completed_steps", []) + ["aggregator"],
    }