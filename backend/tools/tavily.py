"""
tavily.py
Small wrapper around Tavily's search API for two research needs: recent
news/sentiment, and competitive landscape / market context. Python port of
`src/tools/tavily.js`.

Kept as two separate functions because they use different query templates
and recency settings — that also maps naturally to distinct LangGraph
nodes that can run concurrently.
"""

from .http_utils import fetch_with_timeout

TAVILY_URL = "https://api.tavily.com/search"


async def _tavily_search(query, api_key, *, topic="general", time_range=None, max_results=5):
    body = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": max_results,
        "topic": topic,
    }
    if time_range:
        body["time_range"] = time_range

    res = await fetch_with_timeout(TAVILY_URL, method="POST", json_body=body, timeout_s=15.0)
    if res.status_code >= 400:
        raise RuntimeError(f"Tavily search failed ({res.status_code}): {res.text}")

    return res.json()


async def get_company_news(company_name, api_key):
    """Recent news and sentiment about a company."""
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set")

    data = await _tavily_search(
        f"{company_name} stock news recent developments",
        api_key,
        topic="news",
        time_range="month",
        max_results=6,
    )

    return {
        "summary": data.get("answer"),
        "sources": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "score": r.get("score"),
                "publishedDate": r.get("published_date"),
            }
            for r in (data.get("results") or [])
        ],
    }


async def get_market_context(company_name, api_key):
    """Competitive landscape / market position / moat signals."""
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set")

    data = await _tavily_search(
        f"{company_name} competitors market position competitive advantage industry analysis",
        api_key,
        topic="general",
        max_results=6,
    )

    return {
        "summary": data.get("answer"),
        "sources": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "score": r.get("score"),
            }
            for r in (data.get("results") or [])
        ],
    }
