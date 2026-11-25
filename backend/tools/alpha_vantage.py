"""
alpha_vantage.py
Helpers to look up company fundamentals from Alpha Vantage. Python port of
`src/tools/alphaVantage.js`.

Alpha Vantage requires a stock ticker (e.g. "AAPL"), so we first call
SYMBOL_SEARCH to resolve a free-text company name, then call OVERVIEW to
fetch the fundamentals for that ticker.
"""

from .http_utils import fetch_with_timeout

BASE_URL = "https://www.alphavantage.co/query"


def _as_error_message(data):
    """Alpha Vantage sometimes returns HTTP 200 for errors (e.g. rate
    limits) but with a different payload shape ({Note} / {Information} /
    {"Error Message"}). Returns the message if present, else None."""
    return data.get("Information") or data.get("Note") or data.get("Error Message")


async def _resolve_ticker(company_name, api_key):
    """Resolves a free-text company name to its most likely stock ticker.

    Returns {"symbol": str, "name": str} or None.
    """
    params = {"function": "SYMBOL_SEARCH", "keywords": company_name, "apikey": api_key}
    res = await fetch_with_timeout(BASE_URL, params=params, timeout_s=15.0)
    if res.status_code >= 400:
        raise RuntimeError(f"Alpha Vantage SYMBOL_SEARCH failed: {res.status_code}")

    data = res.json()
    err = _as_error_message(data)
    if err:
        raise RuntimeError(f"Alpha Vantage rate limit or error: {err}")

    matches = data.get("bestMatches") or []
    if not matches:
        return None

    # Prefer US equities since the free OVERVIEW endpoint is most reliable
    # for US-listed companies.
    best = next(
        (m for m in matches if m.get("3. type") == "Equity" and m.get("4. region") == "United States"),
        matches[0],
    )
    return {"symbol": best["1. symbol"], "name": best["2. name"]}


async def _fetch_overview(symbol, api_key):
    """Fetches fundamental data (revenue, margins, valuation multiples,
    etc.) for a resolved ticker."""
    params = {"function": "OVERVIEW", "symbol": symbol, "apikey": api_key}
    res = await fetch_with_timeout(BASE_URL, params=params, timeout_s=15.0)
    if res.status_code >= 400:
        raise RuntimeError(f"Alpha Vantage OVERVIEW failed: {res.status_code}")

    data = res.json()
    err = _as_error_message(data)
    if err:
        raise RuntimeError(f"Alpha Vantage rate limit or error: {err}")

    # An empty object means no overview data for this ticker (not an error).
    if not data:
        return None

    # Return only the fields the synthesis/decision nodes need to keep the
    # LLM context compact and reduce token usage.
    return {
        "symbol": data.get("Symbol"),
        "name": data.get("Name"),
        "sector": data.get("Sector"),
        "industry": data.get("Industry"),
        "description": data.get("Description"),
        "marketCapitalization": data.get("MarketCapitalization"),
        "peRatio": data.get("PERatio"),
        "pegRatio": data.get("PEGRatio"),
        "bookValue": data.get("BookValue"),
        "dividendYield": data.get("DividendYield"),
        "epsTTM": data.get("EPS"),
        "revenueTTM": data.get("RevenueTTM"),
        "profitMargin": data.get("ProfitMargin"),
        "operatingMarginTTM": data.get("OperatingMarginTTM"),
        "returnOnEquityTTM": data.get("ReturnOnEquityTTM"),
        "quarterlyRevenueGrowthYOY": data.get("QuarterlyRevenueGrowthYOY"),
        "quarterlyEarningsGrowthYOY": data.get("QuarterlyEarningsGrowthYOY"),
        "fiftyTwoWeekHigh": data.get("52WeekHigh"),
        "fiftyTwoWeekLow": data.get("52WeekLow"),
        "beta": data.get("Beta"),
    }


async def get_company_financials(company_name, api_key):
    """Public entry point used by the LangGraph node. Resolves ticker then
    fetches fundamentals. Returns a fundamentals dict, or raises with a
    clear message."""
    if not api_key:
        raise RuntimeError("ALPHA_VANTAGE_API_KEY is not set")

    ticker = await _resolve_ticker(company_name, api_key)
    if not ticker:
        raise RuntimeError(f'No ticker found for "{company_name}"')

    overview = await _fetch_overview(ticker["symbol"], api_key)
    if not overview:
        raise RuntimeError(
            f'Ticker "{ticker["symbol"]}" resolved but has no fundamentals data '
            f"(may be too small, foreign-listed, or delisted)"
        )

    return overview
