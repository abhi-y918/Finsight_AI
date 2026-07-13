# agents/pipeline.py
# ─────────────────────────────────────────────────────────────────
# LANGGRAPH PIPELINE — Phase 2 (full 6-agent pipeline)
#
# FLOW:
#   START
#     ↓
#   ingestion_agent       ← parse PDF, clean transactions
#     ↓
#   metadata_agent        ← bank name, account holder, period
#     ↓
#   categorization_agent  ← merchant DB + Claude API
#     ↓
#   anomaly_agent         ← spike, duplicate, subscription detection
#     ↓
#   insight_agent         ← rule-based + Claude AI tips
#     ↓
#   aggregator_agent      ← assemble final dashboard JSON
#     ↓
#   END
#
# STATE:
#   Shared dict passed between all agents.
#   Each agent reads what it needs, writes what it produces.
#   No agent calls another directly — LangGraph manages the flow.
# ─────────────────────────────────────────────────────────────────

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.ingestion_agent      import ingestion_agent
from agents.metadata_agent       import metadata_agent
from agents.categorization_agent import categorization_agent
from agents.anomaly_agent        import anomaly_agent
from agents.insight_agent        import insight_agent
from agents.aggregator_agent     import aggregator_agent


# ── Shared state schema ───────────────────────────────────────────

class PipelineState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────
    file_path:  str
    job_id:     str

    # ── ingestion_agent outputs ───────────────────────────────────
    raw_text:         Optional[str]
    bank_format:      Optional[str]
    transactions:     Optional[list]
    ingestion_error:  Optional[str]

    # ── metadata_agent outputs ────────────────────────────────────
    metadata: Optional[dict]

    # ── categorization_agent outputs ──────────────────────────────
    categorized_transactions: Optional[list]
    category_summary:         Optional[list]
    categorization_stats:     Optional[dict]

    # ── anomaly_agent outputs ─────────────────────────────────────
    anomalies: Optional[list]

    # ── insight_agent outputs ─────────────────────────────────────
    insights: Optional[list]

    # ── aggregator_agent outputs ──────────────────────────────────
    result: Optional[dict]

    # ── Pipeline tracking (for /status endpoint) ──────────────────
    current_step:    Optional[str]
    completed_steps: Optional[list]


# ── Step tracker wrapper ──────────────────────────────────────────
# Wraps each agent to update current_step before running.
# The /status endpoint reads current_step from Redis in Phase 2+.

def track(step_name: str, agent_fn):
    """Wrap an agent to log + track the current pipeline step."""
    def tracked(state: PipelineState) -> PipelineState:
        print(f"\n{'='*55}")
        print(f"  STEP: {step_name.upper()}")
        print(f"{'='*55}")

        updated = {
            **state,
            "current_step": step_name,
            "completed_steps": state.get("completed_steps") or [],
        }

        result = agent_fn(updated)

        completed = list(result.get("completed_steps") or [])
        if step_name not in completed:
            completed.append(step_name)

        return {**result, "completed_steps": completed}

    return tracked


# ── Build the LangGraph pipeline ──────────────────────────────────

def build_pipeline():
    """
    Assemble and compile the full 6-agent LangGraph pipeline.

    Returns a compiled graph ready to invoke.
    """
    graph = StateGraph(PipelineState)

    # Register all 6 nodes
    graph.add_node("ingestion",       track("ingestion",       ingestion_agent))
    graph.add_node("extract_metadata",        track("metadata",        metadata_agent))
    graph.add_node("categorization",  track("categorization",  categorization_agent))
    graph.add_node("anomaly",         track("anomaly",         anomaly_agent))
    graph.add_node("insight",         track("insight",         insight_agent))
    graph.add_node("aggregator",      track("aggregator",      aggregator_agent))

    # Define the flow (linear for now)
    graph.set_entry_point("ingestion")
    graph.add_edge("ingestion",      "extract_metadata")
    graph.add_edge("extract_metadata",       "categorization")
    graph.add_edge("categorization", "anomaly")
    graph.add_edge("anomaly",        "insight")
    graph.add_edge("insight",        "aggregator")
    graph.add_edge("aggregator",     END)

    return graph.compile()


# ── Run pipeline ──────────────────────────────────────────────────

def run_pipeline(file_path: str, job_id: str) -> dict:
    """
    Entry point called by the FastAPI route.

    Args:
        file_path: path to uploaded PDF on disk
        job_id:    unique ID for this analysis

    Returns:
        Final result dict from aggregator_agent
    """
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "file_path":  file_path,
        "job_id":     job_id,
        "raw_text":   None,
        "bank_format": None,
        "transactions": None,
        "ingestion_error": None,
        "metadata": None,
        "categorized_transactions": None,
        "category_summary": None,
        "categorization_stats": None,
        "anomalies": None,
        "insights":  None,
        "result":    None,
        "current_step":    "starting",
        "completed_steps": [],
    }

    final_state = pipeline.invoke(initial_state)
    return final_state.get("result", {})