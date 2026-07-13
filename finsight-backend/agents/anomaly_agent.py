# agents/anomaly_agent.py
# ─────────────────────────────────────────────────────────────────
# ANOMALY AGENT — Node 4 in the LangGraph pipeline
#
# RESPONSIBILITY:
#   Find unusual or noteworthy patterns in the transactions.
#   Does NOT use AI — this is pure statistical/rule-based logic.
#   Fast, free, deterministic.
#
# WHAT IT DETECTS:
#
#   1. SPENDING SPIKE
#      A category's total is X% above its own average
#      e.g. Food spend ₹16,430 vs ₹12,450 avg → +32% → flag it
#      (For Phase 1 we use within-statement monthly avg)
#
#   2. LARGE SINGLE TRANSACTION
#      Any single debit above a threshold relative to monthly income
#      e.g. ₹45,000 single payment when income is ₹82,000 → flag it
#
#   3. DUPLICATE TRANSACTIONS
#      Same description + same amount within 3 days → likely duplicate
#      e.g. Netflix charged twice in same week
#
#   4. SUBSCRIPTION OVERLAP
#      Multiple streaming/subscription services active same month
#      e.g. Netflix + Hotstar + SonyLiv all active → wasteful
#
#   5. FREQUENT SMALL TRANSACTIONS
#      20+ transactions to same merchant → possible impulse spending
#      e.g. 23 Swiggy orders in one month
#
# INPUT:  state["categorized_transactions"]
#         state["category_summary"]
#         state["metadata"]
#
# OUTPUT: state["anomalies"]  (list of anomaly objects)
# ─────────────────────────────────────────────────────────────────

from datetime import datetime, timedelta
from collections import defaultdict


# ── Thresholds (tune these based on real data) ────────────────────
SPIKE_THRESHOLD_PCT = 25          # Flag if category is 25%+ above average
LARGE_TXN_INCOME_RATIO = 0.3     # Flag if single txn > 30% of monthly income
DUPLICATE_WINDOW_DAYS = 3        # Look for duplicates within 3 days
FREQUENT_TXN_THRESHOLD = 15      # Flag if 15+ txns to same merchant in period

# Known subscription services (for overlap detection)
SUBSCRIPTION_KEYWORDS = [
    "netflix", "spotify", "hotstar", "prime", "youtube premium",
    "zee5", "sonyliv", "apple music", "gaana", "jiocinema",
    "mxplayer", "voot", "curiosity stream"
]


def detect_spending_spikes(category_summary: list, months: int) -> list:
    """
    Detect categories where spending is significantly above average.

    For a multi-month statement, we compare each month's category spend
    to the average across all months.

    For a single-month statement, we use industry benchmarks:
    - Food: ~25-30% of take-home income is typical
    - Transport: ~10-15%
    - Entertainment: ~5-10%

    Returns list of anomaly dicts.
    """
    anomalies = []

    if months <= 1:
        # Single month — can't compare to average, skip spike detection
        # (Insight agent will handle tips instead)
        return anomalies

    # For multi-month: flag categories where monthly avg seems high
    # We'll refine this in Phase 4 with historical user data
    total_spend = sum(c["amount"] for c in category_summary)

    for cat in category_summary:
        # Flag if any single category is more than 50% of total spend
        # (highly unbalanced budget)
        if cat["percentage"] > 50 and cat["category"] not in ["Housing", "Income"]:
            anomalies.append({
                "type": "spending_spike",
                "severity": "high",
                "category": cat["category"],
                "title": f"{cat['category']} is dominating your budget",
                "description": f"₹{cat['amount']:,.0f} ({cat['percentage']:.0f}% of total spend) went to {cat['category']}. This seems unusually high.",
                "amount": cat["amount"],
                "percentage": cat["percentage"],
            })

    return anomalies


def detect_large_transactions(transactions: list, monthly_income: float) -> list:
    """
    Flag any single debit transaction that is unusually large
    relative to the monthly income.
    """
    anomalies = []
    threshold = monthly_income * LARGE_TXN_INCOME_RATIO

    if threshold <= 0:
        return anomalies

    for txn in transactions:
        if txn.get("type") != "debit":
            continue

        amount = txn.get("debit", 0)
        if amount > threshold and txn.get("category") not in ["Housing", "Banking & transfers"]:
            anomalies.append({
                "type": "large_transaction",
                "severity": "medium",
                "category": txn.get("category", "Others"),
                "title": f"Large payment detected",
                "description": f"₹{amount:,.0f} to '{txn['description']}' on {txn['date']} — this is {amount/monthly_income*100:.0f}% of your monthly income.",
                "amount": amount,
                "date": txn["date"],
                "description_txn": txn["description"],
            })

    return anomalies


def detect_duplicates(transactions: list) -> list:
    """
    Find transactions with the same description and amount
    within a short time window — likely accidental double charges.
    """
    anomalies = []
    debit_txns = [t for t in transactions if t.get("type") == "debit"]

    for i, txn_a in enumerate(debit_txns):
        for txn_b in debit_txns[i+1:]:
            # Same description and same amount?
            if txn_a["description"] != txn_b["description"]:
                continue
            if abs(txn_a["debit"] - txn_b["debit"]) > 1:  # allow ₹1 rounding diff
                continue

            # Within the duplicate window?
            try:
                date_a = datetime.strptime(txn_a["date"], "%Y-%m-%d")
                date_b = datetime.strptime(txn_b["date"], "%Y-%m-%d")
                delta = abs((date_b - date_a).days)

                if delta <= DUPLICATE_WINDOW_DAYS:
                    anomalies.append({
                        "type": "duplicate_transaction",
                        "severity": "high",
                        "category": txn_a.get("category", "Others"),
                        "title": f"Possible duplicate charge",
                        "description": f"'{txn_a['description']}' was charged ₹{txn_a['debit']:,.0f} twice within {delta} days ({txn_a['date']} and {txn_b['date']}). Check if this was intentional.",
                        "amount": txn_a["debit"],
                        "dates": [txn_a["date"], txn_b["date"]],
                    })
                    break  # Only flag once per pair
            except ValueError:
                continue

    return anomalies


def detect_subscription_overlap(transactions: list) -> list:
    """
    Find multiple active streaming/subscription services in the same month.
    Having 3+ at the same time is usually wasteful.
    """
    anomalies = []

    # Find all subscription transactions
    active_subs = []
    for txn in transactions:
        if txn.get("type") != "debit":
            continue
        desc_lower = txn.get("description", "").lower()
        for keyword in SUBSCRIPTION_KEYWORDS:
            if keyword in desc_lower:
                active_subs.append({
                    "name": txn["description"],
                    "amount": txn["debit"],
                    "date": txn["date"],
                })
                break

    # Remove duplicates (same service charged monthly)
    unique_subs = {}
    for sub in active_subs:
        key = sub["name"].lower()[:20]  # use first 20 chars as key
        if key not in unique_subs:
            unique_subs[key] = sub

    unique_list = list(unique_subs.values())

    if len(unique_list) >= 3:
        total_sub_cost = sum(s["amount"] for s in unique_list)
        names = ", ".join(s["name"] for s in unique_list[:3])
        anomalies.append({
            "type": "subscription_overlap",
            "severity": "medium",
            "category": "Entertainment",
            "title": f"{len(unique_list)} subscriptions active simultaneously",
            "description": f"{names} are all active. Combined cost: ₹{total_sub_cost:,.0f}/mo. Consider pausing ones you rarely use.",
            "amount": total_sub_cost,
            "subscriptions": unique_list,
        })

    return anomalies


def detect_frequent_merchant(transactions: list) -> list:
    """
    Flag merchants where the user has an unusually high transaction count.
    Signals potential impulse spending.
    """
    anomalies = []

    # Count transactions per merchant (debits only)
    merchant_counts: dict[str, dict] = defaultdict(lambda: {"count": 0, "total": 0.0})

    for txn in transactions:
        if txn.get("type") != "debit":
            continue
        desc = txn.get("description", "")
        # Use first 20 chars as merchant key (handles slight description variations)
        key = desc[:20].strip()
        merchant_counts[key]["count"] += 1
        merchant_counts[key]["total"] += txn.get("debit", 0)

    for merchant, data in merchant_counts.items():
        if data["count"] >= FREQUENT_TXN_THRESHOLD:
            anomalies.append({
                "type": "frequent_merchant",
                "severity": "low",
                "category": "Others",
                "title": f"High frequency spending at one merchant",
                "description": f"'{merchant}' was charged {data['count']} times totalling ₹{data['total']:,.0f}. This might be worth reviewing.",
                "count": data["count"],
                "amount": data["total"],
                "merchant": merchant,
            })

    return anomalies


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────

def anomaly_agent(state: dict) -> dict:
    """
    LangGraph node: detect spending anomalies and patterns.

    Input state keys:
        categorized_transactions (list)
        category_summary (list)
        metadata (dict)

    Output state keys added:
        anomalies (list): all detected anomalies, sorted by severity
    """
    print("[AnomalyAgent] Starting...")

    transactions = state.get("categorized_transactions", [])
    category_summary = state.get("category_summary", [])
    metadata = state.get("metadata", {})
    months = metadata.get("months", 1)

    # Estimate monthly income from credit transactions
    total_income = sum(t.get("credit", 0) for t in transactions if t.get("type") == "credit")
    monthly_income = total_income / months if months > 0 else total_income

    print(f"[AnomalyAgent] Analyzing {len(transactions)} transactions, {months} month(s), ₹{monthly_income:,.0f}/mo income")

    # Run all detectors
    all_anomalies = []
    all_anomalies += detect_spending_spikes(category_summary, months)
    all_anomalies += detect_large_transactions(transactions, monthly_income)
    all_anomalies += detect_duplicates(transactions)
    all_anomalies += detect_subscription_overlap(transactions)
    all_anomalies += detect_frequent_merchant(transactions)

    # Sort by severity: high → medium → low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))

    print(f"[AnomalyAgent] ✅ Found {len(all_anomalies)} anomalies")
    for a in all_anomalies:
        print(f"  [{a['severity'].upper()}] {a['title']}")

    return {
        **state,
        "anomalies": all_anomalies,
    }