"""
rubric.py
The investment decision rubric the LLM uses to score companies. Direct port
of `src/graph/rubric.js` — wording is unchanged so the agent's behavior
doesn't drift between the JS and Python versions. Edit this file to change
how the agent reasons.
"""

import json

DECISION_RUBRIC = """
You are an investment research analyst. Score the company on these five dimensions,
each from 1 (very weak) to 5 (very strong). Be honest and skeptical — do not default
to the middle. Justify every score with a specific fact from the research provided.

1. GROWTH — revenue/earnings growth trajectory (YoY growth, momentum, market expansion)
2. PROFITABILITY — margins, return on equity, capital efficiency
3. VALUATION — is the current price reasonable relative to fundamentals (P/E, PEG vs sector norms)
4. MOAT — competitive position, differentiation, barriers to entry, pricing power
5. RISK — balance sheet health, sector/regulatory headwinds, controversy, volatility (beta)

If data for a dimension is missing or unclear, score conservatively (3) and say so explicitly
rather than guessing. Never invent numbers that were not in the provided research.
""".strip()


def _format_sources(sources):
    if not sources:
        return "No sources found."
    lines = []
    for i, s in enumerate(sources):
        content = (s.get("content") or "")[:300]
        lines.append(f"[{i + 1}] {s.get('title')} — {content}")
    return "\n".join(lines)


def build_synthesis_prompt(company_name, financials, news, market):
    """Build the prompt for the synthesis node.

    The synthesis node turns raw research into structured scores and
    evidence. It does not make the final verdict; that happens in the
    decision node.
    """
    financials_block = (
        json.dumps(financials, indent=2)
        if financials
        else "NOT AVAILABLE — could not resolve ticker or fetch fundamentals."
    )

    news_summary = f"Summary: {news['summary']}" if news and news.get("summary") else "No summary available."
    market_summary = (
        f"Summary: {market['summary']}" if market and market.get("summary") else "No summary available."
    )

    return f"""{DECISION_RUBRIC}

COMPANY: {company_name}

--- FINANCIAL DATA (Alpha Vantage) ---
{financials_block}

--- RECENT NEWS (Tavily) ---
{news_summary}
{_format_sources(news.get("sources") if news else None)}

--- MARKET / COMPETITIVE CONTEXT (Tavily) ---
{market_summary}
{_format_sources(market.get("sources") if market else None)}

Score each of the 5 dimensions (1-5) with a one-sentence justification citing specific
data above. Then list 2-4 key risks and 2-4 key strengths as short bullet points.
""".strip()


def build_decision_prompt(company_name, analysis):
    """Build the prompt for the decision node.

    The decision node receives the completed analysis and returns one of
    INVEST / PASS / WATCH along with confidence and reasoning.
    """
    return f"""
You are finalizing an investment recommendation for {company_name} based on this
completed analysis:

{json.dumps(analysis, indent=2)}

Decide on exactly one verdict: "INVEST", "PASS", or "WATCH".
- INVEST: strong scores across most dimensions, clear conviction, acceptable risk.
- PASS: weak fundamentals, poor valuation, or red flags that outweigh strengths.
- WATCH: genuinely mixed signals — promising but missing key confirmation
  (e.g. waiting on an earnings report, regulatory decision, or more data).

Provide:
- verdict: one of the three options above
- confidence: a number 0-100 representing how confident you are in this verdict
- reasoning: 3-5 sentences explaining the call, referencing specific scores/data
- whatWouldChangeMyMind: 1-3 sentences on what new information would flip this verdict
""".strip()
