# api/schemas.py — Phase 2 updated schemas

from pydantic import BaseModel
from typing import Optional

class Transaction(BaseModel):
    date:             str
    description:      str
    debit:            float
    credit:           float
    balance:          float
    amount:           float
    type:             str
    category:         Optional[str]  = "Others"
    category_source:  Optional[str]  = "review"   # exact_match/fuzzy_match/pattern_match/ai_match/review
    confidence:       Optional[float] = 0.0

class StatementMetadata(BaseModel):
    bank:              str
    account_holder:    str
    account_number:    str
    period_label:      str
    period_from:       str
    period_to:         str
    months:            int
    total_transactions: int
    categorized_pct:   Optional[int]  = 0
    ai_calls_made:     Optional[int]  = 0

class Summary(BaseModel):
    total_income:       float
    total_spending:     float
    net:                float
    savings:            float
    savings_rate:       float
    monthly_avg_spend:  float
    monthly_avg_income: float
    total_transactions: int

class CategorySummary(BaseModel):
    category:   str
    amount:     float
    count:      int
    percentage: float

class Anomaly(BaseModel):
    type:        str         # spending_spike / duplicate / subscription_overlap etc.
    severity:    str         # high / medium / low
    category:    Optional[str]
    title:       str
    description: str
    amount:      Optional[float] = None

class Insight(BaseModel):
    title:       str
    description: str
    type:        str         # warning / tip / info
    category:    Optional[str] = None
    source:      Optional[str] = None   # rule_based / ai

class AnalysisResult(BaseModel):
    metadata:     StatementMetadata
    summary:      Summary
    categories:   list[CategorySummary]
    transactions: list[Transaction]
    anomalies:    list[Anomaly]
    insights:     list[Insight]
    phase:        int = 2

class AnalyzeResponse(BaseModel):
    job_id:  str
    status:  str
    result:  Optional[AnalysisResult] = None

class StatusResponse(BaseModel):
    job_id:          str
    status:          str
    current_step:    str
    completed_steps: list[str]
    progress_pct:    int

class ErrorResponse(BaseModel):
    error:  str
    detail: Optional[str] = None