"""
state.py
The single shared state object passed between LangGraph nodes. Python port
of `src/graph/state.js`.

Each node receives the full state dict and returns only the keys it
updates; LangGraph merges those partial updates back into the global
state. Fields annotated with `operator.add` are concatenated across
updates (used for `trace` and `errors`, so we keep a running history);
everything else is last-write-wins, matching the JS reducers.
"""

import operator
from typing import Any, Dict, List, Optional

from typing_extensions import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    # ---- INPUT ----
    companyName: str

    # ---- RESEARCH NODE OUTPUTS ----
    # Raw financial fundamentals from Alpha Vantage (None if lookup failed)
    financials: Optional[Dict[str, Any]]

    # Raw news / web search results from Tavily
    newsResults: Optional[Dict[str, Any]]

    # Competitive / market context search results from Tavily
    marketContext: Optional[Dict[str, Any]]

    # ---- ERROR TRACKING ----
    # Nodes append non-fatal errors here so one failing data source doesn't
    # stop the whole research run.
    errors: Annotated[List[str], operator.add]

    # ---- SYNTHESIS NODE OUTPUT ----
    # Structured rubric scores produced by the synthesis node
    analysis: Optional[Dict[str, Any]]

    # ---- FINAL DECISION NODE OUTPUT ----
    verdict: Optional[Dict[str, Any]]

    # ---- OBSERVABILITY ----
    # Human-readable trace of the agent's steps, useful for the UI and for
    # debugging or audit logs.
    trace: Annotated[List[str], operator.add]
