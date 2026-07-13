import json
import os
from rapidfuzz import process, fuzz

MERCHANTS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "merchants.json")

# Load merchants once
_merchants = {}
if os.path.exists(MERCHANTS_FILE):
    with open(MERCHANTS_FILE, "r", encoding="utf-8") as f:
        _merchants = json.load(f)

# Remove metadata keys
_merchants = {k: v for k, v in _merchants.items() if not k.startswith("_")}


def lookup_merchant(description: str) -> dict | None:
    """
    Look up a transaction description in the local merchant database.
    
    1. Exact substring match
    2. Fuzzy match
    3. Pattern match
    """
    if not description:
        return None

    desc_lower = description.lower()

    # 1. Exact Substring Match (e.g. "swiggy" in "UPI/swiggy/12345")
    for merchant, category in _merchants.items():
        if merchant in desc_lower:
            return {
                "category": category,
                "source": "exact_match",
                "confidence": 1.0
            }

    # 2. Fuzzy Match
    # Clean up description for better matching
    clean_desc = desc_lower.replace("upi", "").replace("neft", "").replace("imps", "").replace("/", " ").strip()
    
    # Use rapidfuzz to find closest match
    match = process.extractOne(
        clean_desc, 
        _merchants.keys(), 
        scorer=fuzz.partial_ratio,
        score_cutoff=85  # Needs to be a very strong match
    )

    if match:
        matched_merchant = match[0]
        score = match[1]
        return {
            "category": _merchants[matched_merchant],
            "source": "fuzzy_match",
            "confidence": round(score / 100, 2)
        }

    return None
