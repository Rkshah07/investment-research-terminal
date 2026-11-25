"""
nodes.py
LangGraph node implementations. Each exported function receives the shared
state dict and returns a partial update (or raises for fatal issues).
Python port of `src/graph/nodes.js`.

We catch and record non-fatal errors inside nodes so the agent can
continue reasoning with whatever data is available — similar to a human
analyst working with incomplete information.
"""

import os

from .rubric import build_decision_prompt, build_synthesis_prompt
from .schemas import Analysis, Verdict
from ..tools.alpha_vantage import get_company_financials
from ..tools.tavily import get_company_news, get_market_context

# ---------------------------------------------------------------------------
# RESEARCH NODES — these run concurrently (see graph.py)
# ---------------------------------------------------------------------------


async def fetch_financials_node(state):
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    try:
        financials = await get_company_financials(state["companyName"], api_key)
        return {
            "financials": financials,
            "trace": [f"✓ Financials fetched for {financials['symbol']}"],
        }
    except Exception as err:
        return {
            "financials": None,
            "errors": [f"Financials: {err}"],
            "trace": [f"✗ Financials lookup failed: {err}"],
        }


async def fetch_news_node(state):
    api_key = os.environ.get("TAVILY_API_KEY")
    try:
        news_results = await get_company_news(state["companyName"], api_key)
        return {
            "newsResults": news_results,
            "trace": [f"✓ News fetched ({len(news_results['sources'])} sources)"],
        }
    except Exception as err:
        return {
            "newsResults": None,
            "errors": [f"News: {err}"],
            "trace": [f"✗ News lookup failed: {err}"],
        }


async def fetch_market_context_node(state):
    api_key = os.environ.get("TAVILY_API_KEY")
    try:
        market_context = await get_market_context(state["companyName"], api_key)
        return {
            "marketContext": market_context,
            "trace": [f"✓ Market context fetched ({len(market_context['sources'])} sources)"],
        }
    except Exception as err:
        return {
            "marketContext": None,
            "errors": [f"Market context: {err}"],
            "trace": [f"✗ Market context lookup failed: {err}"],
        }


# ---------------------------------------------------------------------------
# SYNTHESIS NODE — produce structured scores using the rubric
# ---------------------------------------------------------------------------


def make_synthesis_node(llm):
    """
    llm: a LangChain BaseChatModel instance (e.g. ChatGoogleGenerativeAI).
    """
    structured_llm = llm.with_structured_output(Analysis)

    async def synthesis_node(state):
        # If there is no research data at all, skip calling the LLM and
        # return a clear error so we don't ask a model to analyze nothing.
        if not state.get("financials") and not state.get("newsResults") and not state.get("marketContext"):
            return {
                "errors": ["Synthesis: no research data available from any source — cannot analyze"],
                "trace": ["✗ Synthesis skipped — no data to analyze"],
            }

        prompt = build_synthesis_prompt(
            company_name=state["companyName"],
            financials=state.get("financials"),
            news=state.get("newsResults"),
            market=state.get("marketContext"),
        )

        analysis: Analysis = await structured_llm.ainvoke(prompt)

        return {
            "analysis": analysis.model_dump(),
            "trace": ["✓ Synthesis complete — rubric scored"],
        }

    return synthesis_node


# ---------------------------------------------------------------------------
# DECISION NODE — choose INVEST / PASS / WATCH based on analysis
# ---------------------------------------------------------------------------


def make_decision_node(llm):
    structured_llm = llm.with_structured_output(Verdict)

    async def decision_node(state):
        if not state.get("analysis"):
            return {
                "verdict": {
                    "verdict": "PASS",
                    "confidence": 0,
                    "reasoning": (
                        "No analysis was available to base a decision on — research data "
                        "could not be gathered."
                    ),
                    "whatWouldChangeMyMind": (
                        "Successful retrieval of financial, news, or market data for this company."
                    ),
                },
                "trace": ["✗ Decision defaulted to PASS — no analysis available"],
            }

        prompt = build_decision_prompt(company_name=state["companyName"], analysis=state["analysis"])

        verdict: Verdict = await structured_llm.ainvoke(prompt)

        return {
            "verdict": verdict.model_dump(),
            "trace": [f"✓ Decision: {verdict.verdict} (confidence: {verdict.confidence}%)"],
        }

    return decision_node
