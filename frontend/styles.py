"""Custom CSS theme for the AI Investment Research Terminal."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');

:root {
    --bg: #0b0d0a;
    --bg-elev: #121510;
    --bg-card: #161a14;
    --dot: #20251c;
    --border: #272d22;
    --border-strong: #374030;
    --text: #f3f4ef;
    --muted: #9da394;
    --accent: #34c281;
    --invest: #34c281;
    --watch: #e3a23a;
    --pass: #ef6660;
}

.stApp {
    background-color: var(--bg);
    background-image:
        radial-gradient(var(--dot) 1px, transparent 1px),
        radial-gradient(var(--dot) 1px, transparent 1px);
    background-size: 24px 24px;
    background-position: 0 0, 12px 12px;
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

section[data-testid="stSidebar"] {
    background-color: #0e110c;
    border-right: 1px solid var(--border);
}

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

/* Hero header */
.hero-wrap {
    padding: 0.4rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.4rem;
}
.eyebrow-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 999px;
    background: rgba(52, 194, 129, 0.1);
    border: 1px solid rgba(52, 194, 129, 0.28);
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.hero-title {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 3.1rem;
    line-height: 1.05;
    font-weight: 400;
    color: var(--text);
    margin: 0 0 8px 0;
    letter-spacing: -0.01em;
}
.hero-sub {
    color: var(--muted);
    font-size: 0.98rem;
    line-height: 1.55;
    max-width: 720px;
    margin: 0;
}

/* Verdict executive banner */
.exec-banner {
    background: linear-gradient(135deg, #151912 0%, #10130e 100%);
    border: 1px solid var(--border-strong);
    border-radius: 16px;
    padding: 24px 26px;
    margin: 1rem 0 1.2rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
}
.exec-left {
    flex: 1 1 520px;
}
.company-meta-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.ticker-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    background: #20261c;
    border: 1px solid var(--border-strong);
    color: var(--text);
}
.sector-pill {
    font-size: 11.5px;
    color: var(--muted);
    padding: 3px 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
}
.exec-company {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 2.3rem;
    line-height: 1.1;
    margin: 0 0 12px 0;
    color: var(--text);
}
.verdict-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 14px;
}
.verdict-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 6px 14px;
    border-radius: 8px;
}
.verdict-INVEST { color: #34c281; background: rgba(52, 194, 129, 0.14); border: 1px solid rgba(52, 194, 129, 0.4); }
.verdict-WATCH  { color: #e3a23a; background: rgba(227, 162, 58, 0.14); border: 1px solid rgba(227, 162, 58, 0.4); }
.verdict-PASS   { color: #ef6660; background: rgba(239, 102, 96, 0.14); border: 1px solid rgba(239, 102, 96, 0.4); }
.composite-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: var(--muted);
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
}
.exec-reasoning {
    color: #e4e6de;
    font-size: 0.96rem;
    line-height: 1.62;
    margin: 0 0 12px 0;
}
.flip-box {
    background: rgba(255, 255, 255, 0.025);
    border-left: 3px solid var(--border-strong);
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.89rem;
    color: var(--muted);
    line-height: 1.5;
}
.flip-box strong {
    color: var(--text);
}

/* Radar & Rubric Cards */
.radar-card, .panel-card, .range-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.card-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 10px;
}
.rubric-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.rubric-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 8px;
}
.rubric-title {
    font-weight: 600;
    font-size: 0.98rem;
    color: var(--text);
    margin-right: 8px;
}
.rubric-sub {
    font-size: 0.8rem;
    color: var(--muted);
}
.score-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 999px;
    border: 1px solid;
    white-space: nowrap;
}
.score-track {
    width: 100%;
    height: 6px;
    border-radius: 999px;
    background: #23281f;
    overflow: hidden;
    margin-bottom: 8px;
}
.score-fill {
    height: 100%;
    border-radius: 999px;
}
.rubric-just {
    margin: 0;
    font-size: 0.89rem;
    line-height: 1.5;
    color: #cfd4c7;
}

/* Strengths & Risks */
.list-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 20px;
    height: 100%;
}
.list-card-green { border-top: 3px solid var(--invest); }
.list-card-red   { border-top: 3px solid var(--pass); }
.list-card ul {
    margin: 8px 0 0 0;
    padding-left: 18px;
}
.list-card li {
    margin-bottom: 8px;
    color: #dfe3d8;
    font-size: 0.92rem;
    line-height: 1.5;
}

/* KPI Grid */
.kpi-tile {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.kpi-label {
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 4px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.32rem;
    font-weight: 700;
    color: var(--text);
}

/* 52W Range */
.range-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.mono-muted {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    color: var(--muted);
}
.range-values {
    display: flex;
    align-items: center;
    gap: 16px;
}
.range-label {
    font-size: 11px;
    color: var(--muted);
}
.range-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
}
.range-bar-wrap {
    flex: 1;
    height: 8px;
    background: #23281f;
    border-radius: 999px;
    overflow: hidden;
}
.range-bar {
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, #ef6660 0%, #e3a23a 50%, #34c281 100%);
    opacity: 0.85;
}

/* Source cards */
.source-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.source-title {
    font-weight: 600;
    font-size: 0.94rem;
    color: var(--text);
    text-decoration: none;
}
.source-title:hover {
    color: var(--accent);
    text-decoration: underline;
}
.source-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    margin: 4px 0 8px 0;
}
.source-snippet {
    font-size: 0.87rem;
    color: #c8cdc0;
    line-height: 1.5;
    margin: 0;
}

/* Sidebar status */
.key-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.84rem;
    padding: 6px 10px;
    border-radius: 8px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    margin-bottom: 6px;
}
.badge-ok { color: #34c281; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; }
.badge-miss { color: #e3a23a; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; }
</style>
"""
