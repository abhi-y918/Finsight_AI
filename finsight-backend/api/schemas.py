# api/schemas.py
# ─────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS — Data shapes for API requests and responses
#
# WHY PYDANTIC?
#   FastAPI uses Pydantic to automatically:
#   1. VALIDATE incoming requests (wrong type = 422 error with clear message)
#   2. SERIALIZE outgoing responses (dict → JSON)
#   3. DOCUMENT the API (auto-generates OpenAPI/Swagger docs)
#
# Think of schemas as "contracts":
#   - What the frontend SENDS us
#   - What we SEND BACK to the frontend
# ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional


# ── Response: single transaction ─────────────────────────────────

class Transaction(BaseModel):
    date: str                          # "2025-06-27"
    description: str                   # "Swiggy Technologies"
    debit: float                       # 648.0
    credit: float                      # 0.0
    balance: float                     # 24350.0
    type: str                          # "debit" or "credit"
    amount: float                      # 648.0 (absolute value)
    category: Optional[str] = None     # "Food & dining" (Phase 2)
    category_source: Optional[str] = None  # "db_match" / "ai_match" / "review"
    confidence: Optional[float] = None     # 0.0 - 1.0 (Phase 2)


# ── Response: metadata ───────────────────────────────────────────

class StatementMetadata(BaseModel):
    bank: str                          # "HDFC Bank Ltd"
    account_holder: str                # "Abhinav Yadav"
    account_number: str                # "XXXX1234"
    period_label: str                  # "Jun – Sep 2025"
    period_from: str                   # "Jun 2025"
    period_to: str                     # "Sep 2025"
    months: int                        # 4
    total_transactions: int            # 84


# ── Response: summary ────────────────────────────────────────────

class Summary(BaseModel):
    total_transactions: int
    total_spending: float
    total_income: float
    net: float


# ── Main analysis result ─────────────────────────────────────────

class AnalysisResult(BaseModel):
    metadata: StatementMetadata
    transactions: list[Transaction]
    summary: Summary
    categories: list = []             # Phase 2
    anomalies: list = []              # Phase 2
    insights: list = []               # Phase 2
    phase: int = 1


# ── POST /analyze response ───────────────────────────────────────
# Phase 1: synchronous — returns result immediately
# Phase 2: async — returns job_id, frontend polls /status

class AnalyzeResponse(BaseModel):
    job_id: str
    status: str                        # "processing" or "complete"
    result: Optional[AnalysisResult] = None   # Phase 1: included immediately


# ── GET /status response ─────────────────────────────────────────

class StatusResponse(BaseModel):
    job_id: str
    status: str                        # "processing", "complete", "failed"
    current_step: str                  # "ingestion", "metadata", "categorization"...
    completed_steps: list[str]
    progress_pct: int                  # 0-100


# ── Error response ───────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None