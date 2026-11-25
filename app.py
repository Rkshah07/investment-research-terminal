"""
app.py
Enhanced Streamlit frontend for the AI Investment Research Agent.

Run locally:
    streamlit run app.py

Deploy on Streamlit Community Cloud:
    Push this repo, point the app at app.py, and set GOOGLE_API_KEY,
    TAVILY_API_KEY, and ALPHA_VANTAGE_API_KEY under App settings -> Secrets.
"""

import asyncio
import hashlib
import html
import os
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.graph.graph import build_investment_research_graph
from frontend.charts import (
    render_52w_range_html,
    render_confidence_gauge_svg,
    render_radar_chart_svg,
    render_score_row_html,
    verdict_color,
)
from frontend.formatters import (
    RUBRIC_DIMENSIONS,
    build_json_report,
    build_markdown_report,
    compute_composite_score,
    format_currency,
    format_large_currency,
    format_percent,
    format_ratio,
    get_sample_reports,
    safe_float,
)
from frontend.styles import CUSTOM_CSS

load_dotenv()

st.set_page_config(
    page_title="Investment Research Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

QUICK_COMPANIES = ["NVIDIA", "Apple", "Tesla", "Microsoft", "Zomato"]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


# ---------------------------------------------------------------------------
# Environment & Secret Helpers
# ---------------------------------------------------------------------------
def _sync_secrets_to_env() -> None:
    """Copy Streamlit Cloud secrets into os.environ when present."""
    for key in ("GOOGLE_API_KEY", "TAVILY_API_KEY", "ALPHA_VANTAGE_API_KEY"):
        if not os.environ.get(key):
            try:
                if key in st.secrets and st.secrets[key]:
                    os.environ[key] = str(st.secrets[key])
            except Exception:
                pass


_sync_secrets_to_env()


@st.cache_resource(show_spinner=False)
def _get_compiled_graph(model_name: str, temperature: float, key_fingerprint: str):
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
    )
    return build_investment_research_graph(llm)


def get_graph(model_name: str, temperature: float):
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None
    fingerprint = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]
    return _get_compiled_graph(model_name, temperature, fingerprint)


def run_async(coro):
    """Run an async coroutine safely from Streamlit's sync script thread."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def stream_research(graph_app, company_name: str, status_container) -> Dict[str, Any]:
    """Stream LangGraph node updates into the live Streamlit status box."""
    final_state: Dict[str, Any] = {
        "companyName": company_name,
        "trace": [],
        "errors": [],
    }
    node_labels = {
        "fetchFinancials": "Alpha Vantage Fundamentals",
        "fetchNews": "Tavily Recent News",
        "fetchMarketContext": "Tavily Market Context",
        "synthesis": "5-Factor Rubric Synthesis",
        "decision": "Final Investment Verdict",
    }

    async for chunk in graph_app.astream({"companyName": company_name}):
        for node_name, update in chunk.items():
            label = node_labels.get(node_name, node_name)
            for line in update.get("trace") or []:
                status_container.write(f"**{label}:** {line}")
            final_state = {
                **final_state,
                **update,
                "trace": final_state["trace"] + (update.get("trace") or []),
                "errors": final_state["errors"] + (update.get("errors") or []),
            }
    return final_state


def _safe_url(url: Optional[str]) -> str:
    if not url:
        return "#"
    stripped = url.strip()
    if stripped.startswith(("https://", "http://")):
        return html.escape(stripped, quote=True)
    return "#"


def _init_session_state() -> None:
    if "history" not in st.session_state:
        st.session_state["history"] = {}
    if "active_company" not in st.session_state:
        st.session_state["active_company"] = None
    if "company_input" not in st.session_state:
        st.session_state["company_input"] = ""


_init_session_state()


# ---------------------------------------------------------------------------
# Sidebar — Settings, API Keys, Sample Mode, Session History
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Control Center")

    selected_model = st.selectbox("Gemini Model", GEMINI_MODELS, index=0)
    temperature = st.slider(
        "Reasoning Temperature",
        min_value=0.0,
        max_value=0.7,
        value=0.2,
        step=0.05,
        help="Lower values produce more consistent, data-grounded rubric scores.",
    )

    st.markdown("---")
    st.markdown("#### Data & LLM Keys")
    for env_key, label in (
        ("GOOGLE_API_KEY", "Gemini API"),
        ("TAVILY_API_KEY", "Tavily Search"),
        ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage"),
    ):
        is_set = bool(os.environ.get(env_key))
        badge = '<span class="badge-ok">READY</span>' if is_set else '<span class="badge-miss">MISSING</span>'
        st.markdown(
            f'<div class="key-row"><span>{label}</span>{badge}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Enter / Override Session Keys"):
        g_key = st.text_input("GOOGLE_API_KEY", type="password", key="input_google_key")
        t_key = st.text_input("TAVILY_API_KEY", type="password", key="input_tavily_key")
        a_key = st.text_input("ALPHA_VANTAGE_API_KEY", type="password", key="input_av_key")
        if g_key:
            os.environ["GOOGLE_API_KEY"] = g_key.strip()
        if t_key:
            os.environ["TAVILY_API_KEY"] = t_key.strip()
        if a_key:
            os.environ["ALPHA_VANTAGE_API_KEY"] = a_key.strip()
        st.caption("Keys entered here are kept in memory for this session only.")

    st.markdown("---")
    st.markdown("#### Instant Demo Reports")
    st.caption("Preview the full dashboard without calling external APIs.")
    demo_cols = st.columns(2)
    sample_reports = get_sample_reports()
    if demo_cols[0].button("NVIDIA", use_container_width=True):
        st.session_state["history"]["NVIDIA (Sample)"] = sample_reports["NVIDIA"]
        st.session_state["active_company"] = "NVIDIA (Sample)"
    if demo_cols[1].button("Tesla", use_container_width=True):
        st.session_state["history"]["Tesla (Sample)"] = sample_reports["Tesla"]
        st.session_state["active_company"] = "Tesla (Sample)"

    if st.session_state["history"]:
        st.markdown("---")
        st.markdown("#### Session History")
        history_keys = list(reversed(list(st.session_state["history"].keys())))
        chosen = st.radio(
            "Select a researched company",
            history_keys,
            index=history_keys.index(st.session_state["active_company"])
            if st.session_state["active_company"] in history_keys
            else 0,
            label_visibility="collapsed",
        )
        st.session_state["active_company"] = chosen
        if st.button("Clear History", use_container_width=True):
            st.session_state["history"] = {}
            st.session_state["active_company"] = None
            st.rerun()

    st.markdown("---")
    st.caption("Educational project only. Not financial advice.")


# ---------------------------------------------------------------------------
# Main Hero & Search Bar
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-wrap">
      <div class="eyebrow-pill">LangGraph Multi-Agent Pipeline · 5-Factor Rubric</div>
      <h1 class="hero-title">Investment Research Terminal</h1>
      <p class="hero-sub">
        Concurrent fundamental, news, and competitive intelligence synthesis powered by
        Gemini, Alpha Vantage, and Tavily — validated via structured Pydantic scoring.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick-pick chips above the form
chip_cols = st.columns([1.4, 1, 1, 1, 1, 1])
chip_cols[0].markdown(
    "<div style='padding-top:7px;color:#9da394;font-size:0.84rem;'>Quick picks:</div>",
    unsafe_allow_html=True,
)
quick_selected: Optional[str] = None
for idx, ticker_name in enumerate(QUICK_COMPANIES, start=1):
    if chip_cols[idx].button(ticker_name, key=f"chip_{ticker_name}", use_container_width=True):
        st.session_state["company_input"] = ticker_name
        quick_selected = ticker_name

with st.form("research_form", clear_on_submit=False):
    form_col1, form_col2 = st.columns([4.2, 1.2])
    company_name = form_col1.text_input(
        "Company name or ticker",
        key="company_input",
        placeholder="e.g. NVIDIA, Apple, Microsoft, Tesla, Zomato...",
        label_visibility="collapsed",
    )
    submitted = form_col2.form_submit_button("Run Research", type="primary", use_container_width=True)

target_company = quick_selected or (company_name.strip() if submitted else None)

if submitted or quick_selected:
    if not target_company:
        st.warning("Enter a company name first.")
    elif not os.environ.get("GOOGLE_API_KEY"):
        st.error(
            "GOOGLE_API_KEY is not configured. Add it to `.env` or enter it in the "
            "sidebar **Enter / Override Session Keys** panel — or click a **Sample** button in the sidebar."
        )
    else:
        graph_app = get_graph(selected_model, temperature)
        with st.status(f"Researching **{target_company}**...", expanded=True) as status:
            try:
                result = run_async(stream_research(graph_app, target_company, status))
                status.update(label=f"Research complete for {target_company}", state="complete", expanded=False)
                st.session_state["history"][target_company] = result
                st.session_state["active_company"] = target_company
            except Exception as err:
                status.update(label=f"Research failed for {target_company}", state="error", expanded=True)
                st.error(f"Research agent failed: {err}")


# ---------------------------------------------------------------------------
# Active Report Rendering
# ---------------------------------------------------------------------------
active_key = st.session_state.get("active_company")
result = st.session_state["history"].get(active_key) if active_key else None

if not result:
    st.markdown(
        """
        <div class="panel-card" style="text-align:center;padding:34px 24px;margin-top:14px;">
          <div class="card-kicker">Ready to Analyze</div>
          <h3 style="margin:0 0 8px 0;font-weight:600;">Enter any public company above to begin</h3>
          <p style="color:#9da394;max-width:560px;margin:0 auto;">
            The pipeline runs Alpha Vantage fundamentals and two Tavily intelligence searches in parallel,
            scores 5 investment factors, and issues a confidence-weighted INVEST / WATCH / PASS verdict.
            Want to preview the UI immediately? Load <strong>NVIDIA</strong> or <strong>Tesla</strong> under
            <em>Instant Demo Reports</em> in the sidebar.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


financials = result.get("financials") or {}
analysis = result.get("analysis") or {}
verdict = result.get("verdict") or {}
news_results = result.get("newsResults") or {}
market_context = result.get("marketContext") or {}
errors = result.get("errors") or []

display_name = financials.get("name") or result.get("companyName") or active_key
symbol = financials.get("symbol") or "N/A"
sector = financials.get("sector") or "Sector unavailable"
industry = financials.get("industry") or ""
mcap_str = format_large_currency(financials.get("marketCapitalization"))
composite = compute_composite_score(analysis)

if result.get("isSample"):
    st.info("Viewing an **Instant Demo Report** with sample data. Enter your API keys in the sidebar to run live research.")

if errors:
    with st.expander(f"Partial data notice ({len(errors)} source warning{'s' if len(errors) > 1 else ''})", expanded=True):
        st.caption("Remaining sources were preserved and factored conservatively into the verdict.")
        for e in errors:
            st.warning(e)

# ---------------------------------------------------------------------------
# Executive Verdict Banner + Export Controls
# ---------------------------------------------------------------------------
v_label = verdict.get("verdict", "WATCH")
confidence = int(verdict.get("confidence", 0) or 0)
reasoning = verdict.get("reasoning", "No reasoning available.")
flip_text = verdict.get("whatWouldChangeMyMind", "N/A")

meta_pills = [f'<span class="ticker-badge">{html.escape(str(symbol))}</span>']
if sector:
    sector_text = f"{sector}" + (f" · {industry}" if industry else "")
    meta_pills.append(f'<span class="sector-pill">{html.escape(sector_text)}</span>')
if mcap_str != "—":
    meta_pills.append(f'<span class="sector-pill">MCap {html.escape(mcap_str)}</span>')

gauge_svg = render_confidence_gauge_svg(confidence, v_label)

st.markdown(
    f"""
    <div class="exec-banner">
      <div class="exec-left">
        <div class="company-meta-row">{''.join(meta_pills)}</div>
        <h2 class="exec-company">{html.escape(str(display_name))}</h2>
        <div class="verdict-row">
          <span class="verdict-pill verdict-{html.escape(v_label)}">VERDICT: {html.escape(v_label)}</span>
          <span class="composite-chip">Composite Rubric: {composite:.1f} / 5.0</span>
        </div>
        <p class="exec-reasoning">{html.escape(reasoning)}</p>
        <div class="flip-box">
          <strong>What would change this verdict:</strong> {html.escape(flip_text)}
        </div>
      </div>
      <div>{gauge_svg}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

dl_col1, dl_col2, _ = st.columns([1.3, 1.3, 3.4])
safe_slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(display_name)).strip("_") or "report"
dl_col1.download_button(
    "Download Markdown Brief",
    data=build_markdown_report(result),
    file_name=f"{safe_slug}_research_brief.md",
    mime="text/markdown",
    use_container_width=True,
)
dl_col2.download_button(
    "Export Raw JSON",
    data=build_json_report(result),
    file_name=f"{safe_slug}_research_data.json",
    mime="application/json",
    use_container_width=True,
)


# ---------------------------------------------------------------------------
# Multi-Tab Dashboard
# ---------------------------------------------------------------------------
tab_names = [
    "Scorecard & Thesis",
    "Financial Fundamentals",
    "News & Market Intel",
    "Pipeline Trace & Raw",
]
if len(st.session_state["history"]) >= 2:
    tab_names.append("Compare Runs")

tabs = st.tabs(tab_names)

# ---- TAB 1: SCORECARD & THESIS ----
with tabs[0]:
    if analysis:
        left_col, right_col = st.columns([1.0, 1.25], gap="large")
        with left_col:
            radar_scores = [
                (label, int(analysis.get(f"{key}Score", 0) or 0))
                for key, label, _ in RUBRIC_DIMENSIONS
            ]
            st.markdown(
                render_radar_chart_svg(radar_scores, accent=verdict_color(v_label)),
                unsafe_allow_html=True,
            )

        with right_col:
            for key, label, subtitle in RUBRIC_DIMENSIONS:
                score = int(analysis.get(f"{key}Score", 1) or 1)
                just = analysis.get(f"{key}Justification", "")
                st.markdown(
                    render_score_row_html(label, subtitle, score, just),
                    unsafe_allow_html=True,
                )

        s_col, r_col = st.columns(2, gap="medium")
        with s_col:
            strengths_li = "".join(
                f"<li>{html.escape(str(item))}</li>" for item in (analysis.get("strengths") or [])
            )
            st.markdown(
                f"""
                <div class="list-card list-card-green">
                  <div class="card-kicker" style="color:#34c281;">Key Strengths</div>
                  <ul>{strengths_li}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r_col:
            risks_li = "".join(
                f"<li>{html.escape(str(item))}</li>" for item in (analysis.get("risks") or [])
            )
            st.markdown(
                f"""
                <div class="list-card list-card-red">
                  <div class="card-kicker" style="color:#ef6660;">Key Risks</div>
                  <ul>{risks_li}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Rubric synthesis was skipped because no upstream research data was available.")


# ---- TAB 2: FINANCIAL FUNDAMENTALS ----
with tabs[1]:
    if financials:
        kpis = [
            ("Market Cap", format_large_currency(financials.get("marketCapitalization"))),
            ("Revenue (TTM)", format_large_currency(financials.get("revenueTTM"))),
            ("P/E Ratio", format_ratio(financials.get("peRatio"), "x")),
            ("PEG Ratio", format_ratio(financials.get("pegRatio"), "x")),
            ("EPS (TTM)", format_currency(financials.get("epsTTM"))),
            ("Profit Margin", format_percent(financials.get("profitMargin"))),
            ("Operating Margin", format_percent(financials.get("operatingMarginTTM"))),
            ("Return on Equity", format_percent(financials.get("returnOnEquityTTM"))),
            ("Rev Growth (YoY)", format_percent(financials.get("quarterlyRevenueGrowthYOY"))),
            ("EPS Growth (YoY)", format_percent(financials.get("quarterlyEarningsGrowthYOY"))),
            ("Dividend Yield", format_percent(financials.get("dividendYield"))),
            ("Beta", format_ratio(financials.get("beta"))),
        ]
        for row_start in range(0, len(kpis), 4):
            row_cols = st.columns(4)
            for col, (k_label, k_val) in zip(row_cols, kpis[row_start : row_start + 4]):
                col.markdown(
                    f"""
                    <div class="kpi-tile">
                      <div class="kpi-label">{html.escape(k_label)}</div>
                      <div class="kpi-value">{html.escape(k_val)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        low_52 = safe_float(financials.get("fiftyTwoWeekLow"))
        high_52 = safe_float(financials.get("fiftyTwoWeekHigh"))
        range_html = render_52w_range_html(low_52, high_52)
        if range_html:
            st.markdown(range_html, unsafe_allow_html=True)

        desc = financials.get("description")
        if desc:
            st.markdown(
                f"""
                <div class="panel-card">
                  <div class="card-kicker">Company Profile</div>
                  <p style="margin:0;color:#d6dbd0;line-height:1.6;font-size:0.93rem;">
                    {html.escape(str(desc))}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning(
            "Financial fundamentals from Alpha Vantage were unavailable for this run "
            "(missing API key, rate limit, or non-US/unlisted ticker)."
        )


# ---- TAB 3: NEWS & MARKET INTEL ----
def _render_source_column(title: str, payload: Dict[str, Any], empty_msg: str) -> None:
    if not payload:
        st.info(empty_msg)
        return
    summary = payload.get("summary")
    if summary:
        st.markdown(
            f"""
            <div class="panel-card">
              <div class="card-kicker">{html.escape(title)} Synthesis</div>
              <p style="margin:0;color:#e0e4da;line-height:1.6;font-size:0.93rem;">
                {html.escape(str(summary))}
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    sources = payload.get("sources") or []
    if sources:
        st.markdown(f"**Sources ({len(sources)})**")
        for src in sources:
            s_title = html.escape(str(src.get("title") or "Untitled source"))
            s_url = _safe_url(src.get("url"))
            pub = src.get("publishedDate")
            score = safe_float(src.get("score"))
            meta_parts: List[str] = []
            if pub:
                meta_parts.append(str(pub))
            if score is not None:
                meta_parts.append(f"Relevance {score:.0%}")
            meta_html = html.escape(" · ".join(meta_parts)) if meta_parts else "Web source"
            snippet = html.escape(str(src.get("content") or "")[:280])
            st.markdown(
                f"""
                <div class="source-card">
                  <a class="source-title" href="{s_url}" target="_blank" rel="noopener noreferrer">{s_title}</a>
                  <div class="source-meta">{meta_html}</div>
                  <p class="source-snippet">{snippet}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


with tabs[2]:
    n_col, m_col = st.columns(2, gap="large")
    with n_col:
        _render_source_column(
            "Recent News",
            news_results,
            "Recent news data was unavailable for this run.",
        )
    with m_col:
        _render_source_column(
            "Competitive Landscape",
            market_context,
            "Market context data was unavailable for this run.",
        )


# ---- TAB 4: PIPELINE TRACE & RAW DATA ----
with tabs[3]:
    st.markdown(
        """
        <div class="panel-card">
          <div class="card-kicker">LangGraph Execution Topology</div>
          <div class="mono-muted">
            START → [fetchFinancials || fetchNews || fetchMarketContext] → synthesis → decision → END
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    trace_lines = result.get("trace") or []
    if trace_lines:
        st.code("\n".join(trace_lines), language="text")
    else:
        st.caption("No trace lines recorded.")

    with st.expander("Inspect Raw State JSON"):
        st.json(result)


# ---- TAB 5: COMPARE RUNS (WHEN 2+ COMPANIES ANALYZED) ----
if len(tabs) > 4:
    with tabs[4]:
        st.markdown("#### Side-by-Side Comparison")
        rows = []
        for name, item in st.session_state["history"].items():
            a = item.get("analysis") or {}
            v = item.get("verdict") or {}
            f = item.get("financials") or {}
            rows.append(
                {
                    "Company": name,
                    "Ticker": f.get("symbol") or "—",
                    "Verdict": v.get("verdict") or "—",
                    "Confidence": f"{v.get('confidence', 0)}%" if v else "—",
                    "Composite": f"{compute_composite_score(a):.1f}/5" if a else "—",
                    "Growth": a.get("growthScore", "—"),
                    "Profitability": a.get("profitabilityScore", "—"),
                    "Valuation": a.get("valuationScore", "—"),
                    "Moat": a.get("moatScore", "—"),
                    "Risk": a.get("riskScore", "—"),
                    "Market Cap": format_large_currency(f.get("marketCapitalization")),
                    "P/E": format_ratio(f.get("peRatio"), "x"),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)
