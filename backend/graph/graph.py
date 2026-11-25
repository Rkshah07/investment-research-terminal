"""
graph.py
Build the LangGraph that runs the research pipeline. Python port of
`src/graph/graph.js`.

Layout:
    START -> (fetchFinancials, fetchNews, fetchMarketContext) [concurrent]
             -> synthesis [waits for all three]
             -> decision -> END

Running the three research nodes concurrently saves a lot of wall-clock
time. Synthesis (scoring) and decision (final verdict) stay as two
separate LLM calls so each prompt stays focused and auditable.
"""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    fetch_financials_node,
    fetch_market_context_node,
    fetch_news_node,
    make_decision_node,
    make_synthesis_node,
)
from .state import AgentState


def build_investment_research_graph(llm):
    """
    llm: a LangChain BaseChatModel instance (e.g. ChatGoogleGenerativeAI
    for Gemini).
    """
    synthesis_node = make_synthesis_node(llm)
    decision_node = make_decision_node(llm)

    graph = StateGraph(AgentState)

    graph.add_node("fetchFinancials", fetch_financials_node)
    graph.add_node("fetchNews", fetch_news_node)
    graph.add_node("fetchMarketContext", fetch_market_context_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("decision", decision_node)

    # Fan-out: START branches into all three research nodes at once.
    graph.add_edge(START, "fetchFinancials")
    graph.add_edge(START, "fetchNews")
    graph.add_edge(START, "fetchMarketContext")

    # Fan-in: LangGraph automatically waits for ALL edges into "synthesis"
    # to complete before running it, since all three point to the same node.
    graph.add_edge("fetchFinancials", "synthesis")
    graph.add_edge("fetchNews", "synthesis")
    graph.add_edge("fetchMarketContext", "synthesis")

    graph.add_edge("synthesis", "decision")
    graph.add_edge("decision", END)

    return graph.compile()
