# agents/insight_agent.py
# ─────────────────────────────────────────────────────────────────
# INSIGHT AGENT — Node 5 in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Generate human-readable, actionable financial insights.
#   This is the "so what?" layer on top of the raw numbers.
#
# HOW IT WORKS:
#   1. Builds a clean summary of all data so far
#   2. Makes ONE Claude API call with the full picture
#   3. Claude returns 4-5 specific, actionable insights
#   4. We validate and clean the response
#
# WHY ONE CALL?
#   Instead of calling Claude per transaction (expensive),
#   we batch everything into one prompt.
#   Claude sees the full financial picture and gives
#   HOLISTIC insights — connections across categories.
#
# INSIGHT TYPES:
#   "warning" → something needs attention (spike, duplicate, overlap)
#   "tip"     → actionable saving recommendation
#   "info"    → interesting pattern worth knowing
#
# INPUT:  state["category_summary"]
#         state["anomalies"]
#         state["metadata"]
#         state["categorized_transactions"]
#
# OUTPUT: state["insights"]  (list of insight objects)
# ─────────────────────────────────────────────────────────────────

from services.claude_client import generate_insights


def build_financial_summary(state: dict) -> dict:
    """
    Distill all the state data into a clean summary dict
    that we send to Claude. Keeping it concise = fewer tokens = cheaper.
    """
    transactions = state.get("categorized_transactions", [])
    category_summary = state.get("category_summary", [])
    metadata = state.get("metadata", {})
    anomalies = state.get("anomalies", [])

    # Basic financials
    total_income  = sum(t.get("credit", 0) for t in transactions if t.get("type") == "credit")
    total_spending = sum(t.get("debit", 0)  for t in transactions if t.get("type") == "debit")
    net = total_income - total_spending
    months = metadata.get("months", 1)
    savings_rate = (net / total_income * 100) if total_income > 0 else 0

    # Simplify anomalies for the prompt (don't send full objects)
    anomaly_summaries = [
        {"type": a["type"], "title": a["title"], "severity": a["severity"]}
        for a in anomalies[:5]  # top 5 only
    ]

    return {
        "total_income": round(total_income, 2),
        "total_spending": round(total_spending, 2),
        "net": round(net, 2),
        "savings_rate": round(savings_rate, 1),
        "months": months,
        "period": metadata.get("period_label", ""),
    }


def add_rule_based_insights(
    transactions: list,
    category_summary: list,
    anomalies: list,
    months: int,
) -> list:
    """
    Generate fast, free rule-based insights BEFORE calling Claude.
    These are deterministic — no AI needed.

    Claude insights are holistic/narrative.
    Rule-based insights are precise/numerical.
    Both together give a complete picture.
    """
    insights = []
    total_spending = sum(c["amount"] for c in category_summary)

    # ── Insight: Savings rate ─────────────────────────────────────
    total_income = sum(t.get("credit", 0) for t in transactions if t.get("type") == "credit")
    if total_income > 0:
        savings_rate = (total_income - total_spending) / total_income * 100
        if savings_rate < 20:
            insights.append({
                "title": "Low savings rate",
                "description": f"You saved {savings_rate:.1f}% of your income this period. Financial experts recommend at least 20%. Try to cut discretionary spending.",
                "type": "warning",
                "category": None,
                "source": "rule_based",
            })
        elif savings_rate >= 40:
            insights.append({
                "title": "Excellent savings rate!",
                "description": f"You saved {savings_rate:.1f}% of your income — well above the recommended 20%. Keep it up!",
                "type": "info",
                "category": None,
                "source": "rule_based",
            })

    # ── Insight: Top spending category ───────────────────────────
    if category_summary:
        top = category_summary[0]
        if top["percentage"] > 35 and top["category"] not in ["Housing"]:
            insights.append({
                "title": f"{top['category']} is your biggest spend",
                "description": f"₹{top['amount']:,.0f} ({top['percentage']:.0f}% of spending) went to {top['category']} across {top['count']} transactions.",
                "type": "warning" if top["percentage"] > 40 else "info",
                "category": top["category"],
                "source": "rule_based",
            })

    # ── Insight: Unclassified transactions ───────────────────────
    review_count = sum(1 for t in transactions if t.get("category_source") == "review")
    if review_count > 0:
        insights.append({
            "title": f"{review_count} transactions need review",
            "description": f"{review_count} transactions couldn't be categorized automatically. Review them to improve your spending breakdown accuracy.",
            "type": "info",
            "category": "Others",
            "source": "rule_based",
        })

    return insights


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────

def insight_agent(state: dict) -> dict:
    """
    LangGraph node: generate AI + rule-based financial insights.

    Input state keys:
        categorized_transactions (list)
        category_summary (list)
        anomalies (list)
        metadata (dict)

    Output state keys added:
        insights (list): combined rule-based + AI insights
    """
    print("[InsightAgent] Starting...")

    transactions = state.get("categorized_transactions", [])
    category_summary = state.get("category_summary", [])
    anomalies = state.get("anomalies", [])
    metadata = state.get("metadata", {})
    months = metadata.get("months", 1)

    # ── Step 1: Fast rule-based insights (free) ──────────────────
    rule_insights = add_rule_based_insights(
        transactions, category_summary, anomalies, months
    )
    print(f"[InsightAgent] Generated {len(rule_insights)} rule-based insights")

    # ── Step 2: AI insights from Claude (paid, holistic) ─────────
    ai_insights = []
    try:
        summary = build_financial_summary(state)
        ai_insights = generate_insights(
            summary=summary,
            categories=category_summary[:6],   # top 6 categories
            anomalies=anomalies[:3],            # top 3 anomalies
        )
        print(f"[InsightAgent] Claude generated {len(ai_insights)} AI insights")

        # Tag them as AI-generated
        for insight in ai_insights:
            insight["source"] = "ai"

    except Exception as e:
        print(f"[InsightAgent] ⚠ Claude insight generation failed: {e}")
        print("[InsightAgent] Continuing with rule-based insights only")

    # ── Step 3: Merge and deduplicate ────────────────────────────
    # Rule-based first (more precise), AI after (more narrative)
    # Limit to 6 total so dashboard doesn't overflow
    all_insights = rule_insights + ai_insights
    all_insights = all_insights[:6]

    print(f"[InsightAgent] ✅ Final insights: {len(all_insights)} total")

    return {
        **state,
        "insights": all_insights,
    }