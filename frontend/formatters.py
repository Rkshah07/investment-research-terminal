"""Formatting, export, and demo-data helpers for the Streamlit frontend."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


RUBRIC_DIMENSIONS = [
    ("growth", "Growth", "Revenue & earnings trajectory"),
    ("profitability", "Profitability", "Margins, ROE & capital efficiency"),
    ("valuation", "Valuation", "Price relative to fundamentals"),
    ("moat", "Moat", "Competitive advantage & barriers"),
    ("risk", "Risk", "Financial, sector & regulatory safety"),
]


def safe_float(value: Any) -> Optional[float]:
    """Convert Alpha Vantage string values ('None', '-', '12.34') safely."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "n/a", "-", "null"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_large_currency(value: Any) -> str:
    """Format large dollar amounts like Market Cap or Revenue TTM."""
    num = safe_float(value)
    if num is None:
        return "—"
    abs_num = abs(num)
    sign = "-" if num < 0 else ""
    if abs_num >= 1e12:
        return f"{sign}${abs_num / 1e12:.2f}T"
    if abs_num >= 1e9:
        return f"{sign}${abs_num / 1e9:.2f}B"
    if abs_num >= 1e6:
        return f"{sign}${abs_num / 1e6:.2f}M"
    if abs_num >= 1e3:
        return f"{sign}${abs_num / 1e3:.1f}K"
    return f"{sign}${abs_num:,.2f}"


def format_percent(value: Any, already_percent: bool = False) -> str:
    """Format decimal ratios (0.245 -> 24.5%) or percentages."""
    num = safe_float(value)
    if num is None:
        return "—"
    pct = num if already_percent else num * 100.0
    return f"{pct:.1f}%"


def format_ratio(value: Any, suffix: str = "") -> str:
    """Format multiples like P/E, PEG, EPS, Beta."""
    num = safe_float(value)
    if num is None:
        return "—"
    return f"{num:.2f}{suffix}"


def format_currency(value: Any) -> str:
    """Format per-share prices or EPS."""
    num = safe_float(value)
    if num is None:
        return "—"
    return f"${num:,.2f}"


def compute_composite_score(analysis: Optional[Dict[str, Any]]) -> float:
    """Compute average score (1.0 - 5.0) across the 5 rubric dimensions."""
    if not analysis:
        return 0.0
    scores = [
        float(analysis.get(f"{key}Score", 0) or 0)
        for key, _, _ in RUBRIC_DIMENSIONS
    ]
    return sum(scores) / len(RUBRIC_DIMENSIONS)


def build_markdown_report(result: Dict[str, Any]) -> str:
    """Build a clean, portable Markdown investment brief for download."""
    company = result.get("companyName", "Unknown Company")
    financials = result.get("financials") or {}
    analysis = result.get("analysis") or {}
    verdict = result.get("verdict") or {}
    news = result.get("newsResults") or {}
    market = result.get("marketContext") or {}
    errors = result.get("errors") or []

    symbol = financials.get("symbol")
    title = f"{company} ({symbol})" if symbol else company
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = [
        f"# Investment Research Report: {title}",
        f"*Generated on {timestamp} — Educational analysis, not financial advice.*",
        "",
    ]

    if verdict:
        lines.extend(
            [
                f"## Verdict: **{verdict.get('verdict', 'N/A')}** ({verdict.get('confidence', 0)}% confidence)",
                "",
                verdict.get("reasoning", ""),
                "",
                f"**What would change this verdict:** {verdict.get('whatWouldChangeMyMind', 'N/A')}",
                "",
            ]
        )

    if analysis:
        avg = compute_composite_score(analysis)
        lines.extend(
            [
                f"## Rubric Scorecard (Average: {avg:.1f} / 5.0)",
                "",
                "| Dimension | Score | Justification |",
                "|---|---:|---|",
            ]
        )
        for key, label, _ in RUBRIC_DIMENSIONS:
            score = analysis.get(f"{key}Score", "—")
            just = str(analysis.get(f"{key}Justification", "")).replace("\n", " ")
            lines.append(f"| {label} | {score}/5 | {just} |")

        lines.append("")
        lines.append("### Key Strengths")
        for s in analysis.get("strengths", []):
            lines.append(f"- {s}")

        lines.append("")
        lines.append("### Key Risks")
        for r in analysis.get("risks", []):
            lines.append(f"- {r}")
        lines.append("")

    if financials:
        lines.extend(
            [
                "## Financial Fundamentals",
                "",
                f"- **Sector / Industry:** {financials.get('sector', '—')} / {financials.get('industry', '—')}",
                f"- **Market Cap:** {format_large_currency(financials.get('marketCapitalization'))}",
                f"- **Revenue (TTM):** {format_large_currency(financials.get('revenueTTM'))}",
                f"- **P/E Ratio:** {format_ratio(financials.get('peRatio'), 'x')} | **PEG:** {format_ratio(financials.get('pegRatio'), 'x')}",
                f"- **Profit Margin:** {format_percent(financials.get('profitMargin'))} | **ROE:** {format_percent(financials.get('returnOnEquityTTM'))}",
                f"- **Quarterly Revenue Growth YoY:** {format_percent(financials.get('quarterlyRevenueGrowthYOY'))}",
                "",
            ]
        )

    if news.get("summary"):
        lines.extend(["## Recent News Summary", "", news["summary"], ""])

    if market.get("summary"):
        lines.extend(["## Market & Competitive Context", "", market["summary"], ""])

    if errors:
        lines.extend(["## Data Warnings", ""])
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines)


def build_json_report(result: Dict[str, Any]) -> str:
    """Serialize full research state to formatted JSON."""
    return json.dumps(result, indent=2, ensure_ascii=False)


def get_sample_reports() -> Dict[str, Dict[str, Any]]:
    """Pre-built sample reports so users can explore the UI without API keys."""
    return {
        "NVIDIA": {
            "companyName": "NVIDIA",
            "financials": {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "sector": "TECHNOLOGY",
                "industry": "SEMICONDUCTORS",
                "description": (
                    "NVIDIA Corporation designs accelerated computing platforms, GPUs, "
                    "networking fabrics, and full-stack CUDA software powering AI data "
                    "centers, visualization, and autonomous systems."
                ),
                "marketCapitalization": "3450000000000",
                "peRatio": "54.2",
                "pegRatio": "1.18",
                "bookValue": "2.68",
                "dividendYield": "0.0003",
                "epsTTM": "2.58",
                "revenueTTM": "113270000000",
                "profitMargin": "0.556",
                "operatingMarginTTM": "0.624",
                "returnOnEquityTTM": "1.18",
                "quarterlyRevenueGrowthYOY": "0.94",
                "quarterlyEarningsGrowthYOY": "1.09",
                "fiftyTwoWeekHigh": "152.89",
                "fiftyTwoWeekLow": "66.25",
                "beta": "1.65",
            },
            "newsResults": {
                "summary": (
                    "NVIDIA continues to see strong hyperscaler demand for Blackwell "
                    "rack-scale systems alongside expanding enterprise AI software adoption."
                ),
                "sources": [
                    {
                        "title": "Hyperscalers expand AI capex commitments for next-gen GPU clusters",
                        "url": "https://example.com/nvidia-blackwell-demand",
                        "content": "Cloud providers reaffirmed multi-year infrastructure spending centered on accelerated compute.",
                        "score": 0.94,
                        "publishedDate": "Recent",
                    },
                    {
                        "title": "CUDA ecosystem and networking attach rates drive data center margin resilience",
                        "url": "https://example.com/nvidia-cuda-moat",
                        "content": "InfiniBand and Spectrum-X networking adoption continues to lift full-rack system revenues.",
                        "score": 0.89,
                        "publishedDate": "Recent",
                    },
                ],
            },
            "marketContext": {
                "summary": (
                    "NVIDIA holds a dominant market share in AI training and inference accelerators, "
                    "supported by CUDA lock-in, though custom ASICs from hyperscalers and AMD GPUs "
                    "represent medium-term competitive pressures."
                ),
                "sources": [
                    {
                        "title": "AI Accelerator Competitive Landscape: GPUs vs Custom Silicon",
                        "url": "https://example.com/ai-accelerator-market",
                        "content": "While hyperscalers invest in internal TPUs and Trainium chips, merchant GPU demand remains supply-constrained.",
                        "score": 0.91,
                    }
                ],
            },
            "errors": [],
            "analysis": {
                "growthScore": 5,
                "growthJustification": "Quarterly revenue grew 94% YoY and earnings grew 109% YoY on surging data center demand.",
                "profitabilityScore": 5,
                "profitabilityJustification": "Operating margin of 62.4% and ROE above 100% demonstrate exceptional capital efficiency.",
                "valuationScore": 3,
                "valuationJustification": "A 54.2x trailing P/E is demanding, though a 1.18x PEG indicates growth keeps multiples grounded.",
                "moatScore": 5,
                "moatJustification": "CUDA software ecosystem, NVLink interconnect, and developer lock-in create high switching costs.",
                "riskScore": 3,
                "riskJustification": "Elevated beta (1.65), export restrictions, and customer concentration among hyperscalers create cyclicality risk.",
                "strengths": [
                    "94% YoY revenue growth with 62.4% operating margin",
                    "Deep CUDA software + full-stack networking moat",
                    "PEG ratio of 1.18 balances high headline P/E",
                ],
                "risks": [
                    "High customer concentration in top cloud hyperscalers",
                    "Custom ASIC competition and geopolitical export curbs",
                    "Valuation leaves narrow room for capex digestion",
                ],
            },
            "verdict": {
                "verdict": "INVEST",
                "confidence": 84,
                "reasoning": (
                    "NVIDIA pairs rare triple-digit earnings growth with industry-leading 62.4% operating margins "
                    "and a deeply entrenched CUDA software moat. While the 54.2x P/E reflects optimism, a 1.18 PEG ratio "
                    "and sustained hyperscaler infrastructure demand support long-term compounding."
                ),
                "whatWouldChangeMyMind": (
                    "A sharp pullback in cloud capex guidance, gross margin compression below 65%, or meaningful "
                    "developer migration away from CUDA toward open alternatives."
                ),
            },
            "trace": [
                "✓ Financials fetched for NVDA (sample mode)",
                "✓ News fetched (2 sources, sample mode)",
                "✓ Market context fetched (1 source, sample mode)",
                "✓ Synthesis complete — rubric scored",
                "✓ Decision: INVEST (confidence: 84%)",
            ],
            "isSample": True,
        },
        "Tesla": {
            "companyName": "Tesla",
            "financials": {
                "symbol": "TSLA",
                "name": "Tesla, Inc.",
                "sector": "CONSUMER CYCLICAL",
                "industry": "AUTO MANUFACTURERS",
                "description": (
                    "Tesla designs, manufactures, and sells electric vehicles, battery "
                    "energy storage systems, and solar energy products while developing "
                    "autonomous driving software and robotics."
                ),
                "marketCapitalization": "890000000000",
                "peRatio": "78.5",
                "pegRatio": "3.40",
                "bookValue": "21.85",
                "dividendYield": "0.0",
                "epsTTM": "3.55",
                "revenueTTM": "97690000000",
                "profitMargin": "0.131",
                "operatingMarginTTM": "0.089",
                "returnOnEquityTTM": "0.198",
                "quarterlyRevenueGrowthYOY": "0.078",
                "quarterlyEarningsGrowthYOY": "0.169",
                "fiftyTwoWeekHigh": "358.64",
                "fiftyTwoWeekLow": "138.80",
                "beta": "2.15",
            },
            "newsResults": {
                "summary": (
                    "Tesla's energy storage deployments reached record highs, partially offsetting "
                    "EV price competition and margin compression in core automotive deliveries."
                ),
                "sources": [
                    {
                        "title": "Tesla Energy storage segment posts strong margin expansion",
                        "url": "https://example.com/tesla-energy-growth",
                        "content": "Megapack deployments continue to grow faster than automotive deliveries.",
                        "score": 0.90,
                        "publishedDate": "Recent",
                    }
                ],
            },
            "marketContext": {
                "summary": (
                    "Global EV competition has intensified from BYD and legacy automakers, keeping "
                    "pricing pressured while investors debate the timeline for FSD autonomy monetization."
                ),
                "sources": [
                    {
                        "title": "Global EV Market Share & Autonomy Race",
                        "url": "https://example.com/ev-market-context",
                        "content": "Tesla retains Supercharger network advantages in North America amid aggressive EV price cuts globally.",
                        "score": 0.87,
                    }
                ],
            },
            "errors": [],
            "analysis": {
                "growthScore": 3,
                "growthJustification": "Revenue growth moderated to 7.8% YoY as automotive pricing pressure offset energy storage gains.",
                "profitabilityScore": 3,
                "profitabilityJustification": "Operating margin stands at 8.9% with 19.8% ROE, well below peak EV margin levels.",
                "valuationScore": 2,
                "valuationJustification": "A 78.5x P/E and 3.40x PEG price in substantial future autonomy optionality beyond current auto earnings.",
                "moatScore": 4,
                "moatJustification": "Brand strength, North American Supercharger standard, and vertical battery integration provide durable advantages.",
                "riskScore": 2,
                "riskJustification": "High beta (2.15), EV price wars, and execution/regulatory uncertainty around autonomous robotaxis elevate risk.",
                "strengths": [
                    "Fast-growing high-margin energy storage business",
                    "Vertical integration and Supercharger ecosystem",
                    "Strong balance sheet and AI/FSD optionality",
                ],
                "risks": [
                    "Stretched valuation (78.5x P/E, 3.40x PEG)",
                    "Automotive margin pressure from global EV competition",
                    "High stock volatility (beta 2.15) and autonomy timeline risk",
                ],
            },
            "verdict": {
                "verdict": "WATCH",
                "confidence": 74,
                "reasoning": (
                    "Tesla combines strong long-term optionality in energy storage and autonomy with near-term "
                    "automotive margin compression and modest 7.8% YoY revenue growth. At 78.5x trailing earnings, "
                    "much of the autonomous upside is already priced in, warranting patience for clearer execution."
                ),
                "whatWouldChangeMyMind": (
                    "Sustained automotive gross margin recovery above 20% alongside commercial regulatory approval "
                    "for unsupervised FSD / robotaxi operations, or a meaningful valuation pullback."
                ),
            },
            "trace": [
                "✓ Financials fetched for TSLA (sample mode)",
                "✓ News fetched (1 source, sample mode)",
                "✓ Market context fetched (1 source, sample mode)",
                "✓ Synthesis complete — rubric scored",
                "✓ Decision: WATCH (confidence: 74%)",
            ],
            "isSample": True,
        },
    }
