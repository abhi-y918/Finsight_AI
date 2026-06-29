# agents/pipeline.py
# ─────────────────────────────────────────────────────────────────
# LANGGRAPH PIPELINE — The brain that wires all agents together
#
# WHY LANGGRAPH?
#   LangGraph lets you define agents as NODES in a graph.
#   Each node is just a Python function: (state) → state
#   The graph decides which node runs next.
#   This makes it easy to:
#     - Add new agents without touching existing ones
#     - Retry individual nodes on failure
#     - Run nodes in parallel (Phase 2+)
#     - Inspect state at any point for the /status endpoint
#
# THE PIPELINE (Phase 1):
#
#   START
#     ↓
#   [ingestion_agent]   ← parse PDF, extract transactions
#     ↓
#   [metadata_agent]    ← extract bank, name, period
#     ↓
#   [aggregator_agent]  ← combine everything into final JSON
#     ↓
#   END
#
# Phase 2 will add:
#   [categorization_agent] → [anomaly_agent] → [insight_agent]
#   between metadata and aggregator.
#
# STATE:
#   All agents share ONE dict called "state".
#   Think of it like a whiteboard that agents read from and write to.
#   The TypedDict below defines what can be in that whiteboard.
# ─────────────────────────────────────────────────────────────────

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.ingestion_agent import ingestion_agent
from agents.metadata_agent import metadata_agent


# ── State schema ──────────────────────────────────────────────────
# TypedDict tells Python (and us!) exactly what keys the state can have.
# Optional means that key might not exist yet at the start.
# This is important: ingestion_agent ADDS "transactions" to state.
# metadata_agent can then safely READ "transactions" from state.

class PipelineState(TypedDict):
    # Input (set before pipeline runs)
    file_path: str
    job_id: str

    # Set by ingestion_agent
    raw_text: Optional[str]
    bank_format: Optional[str]
    transactions: Optional[list]
    ingestion_error: Optional[str]

    # Set by metadata_agent
    metadata: Optional[dict]

    # Set by categorization_agent (Phase 2)
    categorized_transactions: Optional[list]

    # Set by anomaly_agent (Phase 2)
    anomalies: Optional[list]

    # Set by insight_agent (Phase 2)
    insights: Optional[list]

    # Set by aggregator_agent
    result: Optional[dict]

    # Pipeline tracking
    current_step: Optional[str]
    completed_steps: Optional[list]


# ── Simple aggregator for Phase 1 ────────────────────────────────
# In Phase 2 this becomes its own file: agents/aggregator_agent.py
# For now it just bundles what we have into the final result dict.

def aggregator_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node: combine all agent outputs into final dashboard JSON.

    In Phase 1 this is simple — just transactions + metadata.
    In Phase 2 it will merge categories, anomalies, insights too.
    """
    print("[AggregatorAgent] Building final result...")

    transactions = state.get("transactions", [])
    metadata = state.get("metadata", {})

    # Basic spend summary for Phase 1
    total_debit = sum(t["debit"] for t in transactions)
    total_credit = sum(t["credit"] for t in transactions)

    result = {
        # Metadata (topbar info)
        "metadata": metadata,

        # Raw transactions (table on dashboard)
        "transactions": transactions,

        # Basic summary
        "summary": {
            "total_transactions": len(transactions),
            "total_spending": round(total_debit, 2),
            "total_income": round(total_credit, 2),
            "net": round(total_credit - total_debit, 2),
        },

        # These will be filled in Phase 2:
        "categories": [],
        "anomalies": [],
        "insights": [],

        # Pipeline info
        "phase": 1,
        "note": "Categories, anomalies, insights coming in Phase 2",
    }

    print(f"[AggregatorAgent] ✅ Result ready — {len(transactions)} transactions, ₹{total_debit:,.0f} spent")

    return {
        **state,
        "result": result,
        "current_step": "complete",
        "completed_steps": state.get("completed_steps", []) + ["aggregator"],
    }


# ── Step tracker wrapper ──────────────────────────────────────────
# We wrap each agent to update "current_step" in state.
# This is what the /status endpoint reads to show progress.

def track(step_name: str, agent_fn):
    """
    Wrap an agent function to track which step is currently running.
    Returns a new function that updates state["current_step"] before running.
    """
    def tracked_agent(state: PipelineState) -> PipelineState:
        print(f"\n{'='*50}")
        print(f"[Pipeline] Running step: {step_name}")
        print(f"{'='*50}")

        # Mark this step as current
        updated_state = {
            **state,
            "current_step": step_name,
            "completed_steps": state.get("completed_steps", []),
        }

        # Run the actual agent
        result = agent_fn(updated_state)

        # Add this step to completed list
        completed = result.get("completed_steps", [])
        if step_name not in completed:
            completed = completed + [step_name]

        return {**result, "completed_steps": completed}

    return tracked_agent


# ── Build the LangGraph ───────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """
    Assemble the LangGraph state machine.

    PHASE 1 graph:
        ingestion → metadata → aggregator → END

    HOW TO READ THIS:
        graph.add_node("name", function)  ← register a node
        graph.add_edge("from", "to")      ← connect nodes
        graph.set_entry_point("name")     ← where to start
    """
    graph = StateGraph(PipelineState)

    # ── Register nodes ────────────────────────────────────────────
    graph.add_node("ingestion",   track("ingestion",   ingestion_agent))
    graph.add_node("metadata",    track("metadata",    metadata_agent))
    graph.add_node("aggregator",  track("aggregator",  aggregator_agent))

    # Phase 2: add these nodes later
    # graph.add_node("categorization", track("categorization", categorization_agent))
    # graph.add_node("anomaly",         track("anomaly",         anomaly_agent))
    # graph.add_node("insight",         track("insight",         insight_agent))

    # ── Connect nodes (define the flow) ──────────────────────────
    graph.set_entry_point("ingestion")
    graph.add_edge("ingestion",  "metadata")
    graph.add_edge("metadata",   "aggregator")
    graph.add_edge("aggregator", END)

    # Phase 2 edges:
    # graph.add_edge("metadata",        "categorization")
    # graph.add_edge("categorization",  "anomaly")
    # graph.add_edge("anomaly",         "insight")
    # graph.add_edge("insight",         "aggregator")

    return graph.compile()


# ── Run the pipeline ──────────────────────────────────────────────

def run_pipeline(file_path: str, job_id: str) -> dict:
    """
    Entry point called by the FastAPI route.
    Builds the graph, sets initial state, runs it, returns result.

    Args:
        file_path: path to the uploaded PDF on disk
        job_id: unique ID for this analysis job

    Returns:
        The final result dict from aggregator_agent
    """
    pipeline = build_pipeline()

    # Initial state — only what we know before running
    initial_state: PipelineState = {
        "file_path": file_path,
        "job_id": job_id,
        "raw_text": None,
        "bank_format": None,
        "transactions": None,
        "ingestion_error": None,
        "metadata": None,
        "categorized_transactions": None,
        "anomalies": None,
        "insights": None,
        "result": None,
        "current_step": "starting",
        "completed_steps": [],
    }

    # Run the full pipeline (synchronous for Phase 1)
    final_state = pipeline.invoke(initial_state)

    return final_state.get("result", {})