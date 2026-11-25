"""
http_utils.py
Wraps httpx's async client with a hard timeout. Python port of
`src/tools/fetchWithTimeout.js`.

WHY this exists:
Free-tier APIs (especially Alpha Vantage) can stall without ever returning
an error — no 4xx, no 5xx, just silence. Without a timeout, a single slow
API call hangs the entire LangGraph run forever, since the synthesis node
awaits all three research nodes. This guarantees every external call
either succeeds or fails within a bounded time, so one bad API can never
freeze the whole agent.
"""

import httpx

class FetchTimeoutError(Exception):
    pass


async def fetch_with_timeout(url, *, method="GET", params=None, json_body=None, timeout_s=15.0):
    """Issue a single HTTP request with a hard timeout.

    Returns the httpx.Response on success. Raises FetchTimeoutError on
    timeout, or lets other httpx exceptions propagate (matching the JS
    version, which only special-cases AbortError/timeouts).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            return await client.request(method, url, params=params, json=json_body)
    except httpx.TimeoutException as err:
        bare_url = url.split("?")[0]
        raise FetchTimeoutError(f"Request timed out after {timeout_s}s: {bare_url}") from err
