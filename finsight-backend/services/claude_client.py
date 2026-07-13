# services/claude_client.py
# ─────────────────────────────────────────────────────────────────
# CLAUDE API CLIENT — Wrapper around Anthropic SDK
#
# WHY A WRAPPER?
#   Instead of calling anthropic.Anthropic() directly in every agent,
#   we have ONE place that handles:
#     - API key loading
#     - Model selection
#     - Error handling & retries
#     - Token usage logging
#     - Response parsing
#
#   If Anthropic changes their SDK tomorrow, we only fix THIS file.
#   All agents stay untouched.
#
# USED BY:
#   - categorization_agent.py  (classify unknown transactions)
#   - insight_agent.py         (generate financial tips)
# ─────────────────────────────────────────────────────────────────

import openai
import json
import time
from config import settings

# Single client instance — reused across all calls
_client = None

def get_client() -> openai.OpenAI:
    """
    Return the shared OpenAI client configured for OpenRouter.
    Creates it on first call (lazy initialization).
    """
    global _client
    if _client is None:
        _client = openai.OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
    return _client


def call_claude(
    prompt: str,
    system: str = "",
    max_tokens: int = 1000,
    expect_json: bool = False,
    retries: int = 2,
) -> str | dict:
    """
    Core function to call Claude API.

    Args:
        prompt:      The user message / question
        system:      System prompt (sets Claude's behavior/role)
        max_tokens:  Max tokens in response (1000 is enough for most tasks)
        expect_json: If True, parse response as JSON and return dict
        retries:     How many times to retry on API failure

    Returns:
        str  if expect_json=False
        dict if expect_json=True

    WHY expect_json?
        When we ask Claude to categorize a transaction, we want:
        {"category": "Food & dining", "confidence": 0.95}
        Not a paragraph of explanation.
        expect_json=True handles parsing + error recovery for us.
    """
    client = get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.AI_MODEL,
                max_tokens=max_tokens,
                messages=messages,
            )

            raw_text = response.choices[0].message.content.strip()

            # Log token usage for cost tracking
            usage = response.usage
            if usage:
                print(f"[OpenRouterClient] Tokens — input: {usage.prompt_tokens}, output: {usage.completion_tokens}")

            if not expect_json:
                return raw_text

            # Parse JSON response
            # Sometimes wrapped in ```json ... ``` markdown
            clean = raw_text
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()

            return json.loads(clean)

        except openai.RateLimitError:
            if attempt < retries:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                print(f"[OpenRouterClient] Rate limited. Waiting {wait}s before retry {attempt+1}...")
                time.sleep(wait)
            else:
                raise

        except json.JSONDecodeError as e:
            print(f"[OpenRouterClient] JSON parse failed: {e}")
            print(f"[OpenRouterClient] Raw response: {raw_text}")
            # Return empty dict so agent can handle gracefully
            return {}

        except Exception as e:
            print(f"[OpenRouterClient] API error: {e}")
            if attempt < retries:
                time.sleep(1)
            else:
                raise

    return {} if expect_json else ""


def categorize_transaction(description: str, amount: float, txn_type: str) -> dict:
    """
    Ask Claude to categorize a single transaction.

    This is called ONLY when merchant DB lookup fails.
    (We don't want to burn API tokens on known merchants like Swiggy)

    Returns:
        {
            "category": "Food & dining",
            "confidence": 0.87,
            "reasoning": "Swiggy is a food delivery platform"
        }
    """
    system = """You are a financial transaction categorizer for Indian bank statements.
Your job is to classify transactions into exactly one of these categories:
- Food & dining
- Transport
- Entertainment
- Health
- Housing
- Shopping
- Bills & utilities
- Banking & transfers
- Income
- Others

Rules:
1. Respond ONLY with valid JSON — no explanation, no markdown
2. UPI transfers to people (e.g. "UPI/Rahul Sharma") → "Banking & transfers"
3. Salary credits → "Income"
4. ATM withdrawals → "Banking & transfers"
5. If truly uncertain → "Others" with low confidence"""

    prompt = f"""Categorize this bank transaction:

Description: {description}
Amount: ₹{amount:.2f}
Type: {txn_type} (debit = money going out, credit = money coming in)

Respond with JSON only:
{{
  "category": "<category name>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one short sentence>"
}}"""

    return call_claude(prompt=prompt, system=system, expect_json=True, max_tokens=150)


def generate_insights(summary: dict, categories: list, anomalies: list) -> list:
    """
    Ask Claude to generate actionable financial insights.

    Called once per analysis — takes the full summary and
    returns a list of insight objects.

    Returns:
        [
            {
                "title": "Food spending spike",
                "description": "...",
                "type": "warning",   # warning / tip / info
                "category": "Food & dining"
            },
            ...
        ]
    """
    system = """You are a personal finance advisor analyzing Indian bank statements.
Generate practical, specific, actionable insights based on the spending data.
Be direct and helpful. Reference actual numbers from the data.
Respond ONLY with a JSON array — no explanation outside the array."""

    prompt = f"""Analyze this financial data and generate 4-5 insights:

SUMMARY:
- Total income: ₹{summary.get('total_income', 0):,.0f}
- Total spending: ₹{summary.get('total_spending', 0):,.0f}
- Savings: ₹{summary.get('net', 0):,.0f} ({summary.get('savings_rate', 0):.1f}% rate)
- Period: {summary.get('months', 1)} month(s)

SPENDING BY CATEGORY:
{json.dumps(categories, indent=2)}

ANOMALIES DETECTED:
{json.dumps(anomalies, indent=2)}

Generate a JSON array of 4-5 insights:
[
  {{
    "title": "Short title (max 5 words)",
    "description": "Specific actionable insight with actual rupee amounts",
    "type": "warning|tip|info",
    "category": "<category name or null>"
  }}
]"""

    result = call_claude(prompt=prompt, system=system, expect_json=True, max_tokens=800)

    # Claude might return a dict with an array inside, or the array directly
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        # Try common wrapper keys
        for key in ["insights", "data", "results"]:
            if key in result and isinstance(result[key], list):
                return result[key]

    return []