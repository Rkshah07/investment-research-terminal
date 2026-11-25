# AI Investment Research Terminal

An AI-powered investment research agent built with **LangGraph**, **Gemini**, **Alpha Vantage**, **Tavily Search**, and an interactive **Streamlit** dashboard. Given a company name or ticker, it concurrently gathers financial fundamentals, recent news, and competitive market intelligence, scores the company on a **5-factor investment rubric**, and issues a structured **INVEST / WATCH / PASS** verdict.

> Educational project only — not financial advice.

---

## Key Features

- **LangGraph Concurrent Pipeline**: Fetches Alpha Vantage fundamentals, Tavily news, and Tavily competitive context in parallel before running structured synthesis and decision nodes.
- **Interactive Streamlit Terminal (`app.py`)**:
  - **Live Streaming Execution**: Real-time node progress via `app.astream(...)`.
  - **Executive Verdict Banner**: Circular confidence gauge, composite rubric score, reasoning, and reversal catalysts.
  - **5-Factor SVG Radar & Scorecard**: Interactive visual breakdown for Growth, Profitability, Valuation, Moat, and Risk with data-backed justifications.
  - **Financial Fundamentals Tab**: KPI cards (Market Cap, Revenue TTM, P/E, PEG, EPS, Margins, ROE, YoY Growth, Beta), 52-week range indicator, and company profile.
  - **News & Market Intelligence Tab**: Synthesized summaries and clickable source cards with relevance scores.
  - **Session History & Side-by-Side Comparison**: Compare analyzed companies across scores, verdicts, and valuation multiples.
  - **Instant Demo Reports**: Preview the full dashboard for NVIDIA and Tesla without API keys.
  - **Report Export**: Download full research briefs as Markdown (`.md`) or raw state JSON (`.json`).
- **Structured Output Validation**: Uses Pydantic schemas (`Analysis`, `Verdict`) to enforce schema-compliant LLM outputs.
- **Graceful Partial-Failure Handling**: If one data source fails or rate-limits, remaining evidence is preserved and factored conservatively into the verdict.
- **CLI Runner (`cli.py`)**: Run and stream the pipeline directly in the terminal.

---

## Architecture

```text
START
  ├──▶ fetchFinancials (Alpha Vantage SYMBOL_SEARCH + OVERVIEW)
  ├──▶ fetchNews (Tavily news search)
  └──▶ fetchMarketContext (Tavily competitive landscape)
          │
          ▼
      synthesis (Gemini + Pydantic Analysis schema)
          │
          ▼
      decision (Gemini + Pydantic Verdict schema)
          │
          ▼
         END
```

---

## Project Structure

```text
investment-research-pipeline/
├── app.py                   # Enhanced Streamlit frontend
├── cli.py                   # Terminal runner with streaming progress
├── list_models.py           # Helper to list available Gemini models
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml          # Dark terminal theme configuration
├── backend/
│   ├── graph/
│   │   ├── graph.py         # LangGraph topology
│   │   ├── nodes.py         # Research, synthesis & decision nodes
│   │   ├── rubric.py        # 5-factor scoring prompts
│   │   ├── schemas.py       # Flat Pydantic schemas for Gemini
│   │   └── state.py         # Shared AgentState TypedDict
│   └── tools/
│       ├── alpha_vantage.py # Ticker resolution + fundamentals
│       ├── tavily.py        # News & market context search
│       └── http_utils.py    # Shared async httpx helper
├── frontend/
│   ├── charts.py            # SVG radar chart, confidence gauge & score bars
│   ├── formatters.py        # Metric formatting, exports & demo reports
│   └── styles.py            # Custom dark-terminal CSS
└── tests/
    └── test_frontend_helpers.py
```

---

## Quickstart

### 1. Install dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API keys

Copy `.env.example` to `.env` and fill in your keys (or enter them directly in the Streamlit sidebar for session-only use):

```env
GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

### 4. Or run via CLI

```bash
python cli.py "NVIDIA"
```

---

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create a new app on [Streamlit Community Cloud](https://share.streamlit.io/) pointing to `app.py`.
3. Add `GOOGLE_API_KEY`, `TAVILY_API_KEY`, and `ALPHA_VANTAGE_API_KEY` under **App settings → Secrets**.

---

## License

MIT License
