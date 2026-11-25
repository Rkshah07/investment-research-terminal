"""Pure SVG & HTML visualization components (zero external charting dependencies)."""

import html
import math
from typing import Any, Dict, List, Optional, Tuple


VERDICT_COLORS = {
    "INVEST": "#34c281",
    "WATCH": "#e3a23a",
    "PASS": "#ef6660",
}


def verdict_color(verdict: str) -> str:
    return VERDICT_COLORS.get((verdict or "").upper(), "#a3a191")


def render_confidence_gauge_svg(confidence: int, verdict: str) -> str:
    """Render an inline SVG radial gauge for the 0-100% verdict confidence."""
    pct = max(0, min(100, int(confidence or 0)))
    color = verdict_color(verdict)
    radius = 44
    circumference = 2 * math.pi * radius
    dash_offset = circumference * (1.0 - pct / 100.0)

    return f"""
    <div class="gauge-wrap" title="Model confidence: {pct}%">
      <svg viewBox="0 0 110 110" width="110" height="110" role="img" aria-label="Confidence {pct}%">
        <circle cx="55" cy="55" r="{radius}" fill="none" stroke="#242920" stroke-width="9" />
        <circle cx="55" cy="55" r="{radius}" fill="none" stroke="{color}" stroke-width="9"
                stroke-linecap="round"
                stroke-dasharray="{circumference:.2f}"
                stroke-dashoffset="{dash_offset:.2f}"
                transform="rotate(-90 55 55)" />
        <text x="55" y="53" text-anchor="middle" fill="#f3f4ef"
              font-family="JetBrains Mono, monospace" font-size="22" font-weight="700">{pct}%</text>
        <text x="55" y="71" text-anchor="middle" fill="#9da394"
              font-family="Inter, sans-serif" font-size="9" letter-spacing="1.2">CONFIDENCE</text>
      </svg>
    </div>
    """


def render_radar_chart_svg(scores: List[Tuple[str, int]], accent: str = "#34c281") -> str:
    """Render a 5-axis SVG radar chart for the 5-factor rubric (1-5 scale)."""
    cx, cy = 190, 165
    max_r = 108
    n = len(scores)
    if n < 3:
        return ""

    def polar_point(index: int, value: float) -> Tuple[float, float]:
        angle = -math.pi / 2 + (2 * math.pi * index) / n
        r = (value / 5.0) * max_r
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    rings_svg = []
    for level in range(1, 6):
        pts = [polar_point(i, level) for i in range(n)]
        pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        stroke = "#31372c" if level == 5 else "#22261e"
        rings_svg.append(
            f'<polygon points="{pts_str}" fill="none" stroke="{stroke}" stroke-width="1" />'
        )
        # Level label along top axis
        lx, ly = polar_point(0, level)
        rings_svg.append(
            f'<text x="{lx + 6:.1f}" y="{ly + 4:.1f}" fill="#6e7566" '
            f'font-size="9" font-family="JetBrains Mono, monospace">{level}</text>'
        )

    axes_svg = []
    labels_svg = []
    for i, (label, val) in enumerate(scores):
        ox, oy = polar_point(i, 5)
        axes_svg.append(
            f'<line x1="{cx}" y1="{cy}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="#262b22" stroke-width="1" />'
        )
        lx, ly = polar_point(i, 6.15)
        anchor = "middle"
        if lx < cx - 20:
            anchor = "end"
        elif lx > cx + 20:
            anchor = "start"
        safe_label = html.escape(label)
        labels_svg.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
            f'fill="#d9ddd0" font-size="11.5" font-weight="600" font-family="Inter, sans-serif">'
            f'{safe_label} ({val})</text>'
        )

    data_pts = [polar_point(i, max(0, min(5, val))) for i, (_, val) in enumerate(scores)]
    data_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    dots_svg = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{accent}" stroke="#0b0d0a" stroke-width="2" />'
        for x, y in data_pts
    )

    return f"""
    <div class="radar-card">
      <div class="card-kicker">5-Factor Footprint</div>
      <svg viewBox="0 0 380 330" width="100%" style="max-width:380px;display:block;margin:0 auto;" role="img" aria-label="Investment Rubric Radar Chart">
        {''.join(rings_svg)}
        {''.join(axes_svg)}
        <polygon points="{data_str}" fill="{accent}" fill-opacity="0.22" stroke="{accent}" stroke-width="2.2" />
        {dots_svg}
        {''.join(labels_svg)}
      </svg>
    </div>
    """


def render_score_row_html(label: str, subtitle: str, score: int, justification: str) -> str:
    """Render an individual rubric dimension card with a horizontal score bar."""
    clamped = max(1, min(5, int(score or 1)))
    pct = (clamped / 5.0) * 100
    if clamped >= 4:
        bar_color = "#34c281"
    elif clamped == 3:
        bar_color = "#e3a23a"
    else:
        bar_color = "#ef6660"

    return f"""
    <div class="rubric-item">
      <div class="rubric-head">
        <div>
          <span class="rubric-title">{html.escape(label)}</span>
          <span class="rubric-sub">{html.escape(subtitle)}</span>
        </div>
        <span class="score-pill" style="color:{bar_color};border-color:{bar_color}44;background:{bar_color}18;">
          {clamped} / 5
        </span>
      </div>
      <div class="score-track">
        <div class="score-fill" style="width:{pct:.0f}%;background:{bar_color};"></div>
      </div>
      <p class="rubric-just">{html.escape(justification or '')}</p>
    </div>
    """


def render_52w_range_html(low: Optional[float], high: Optional[float]) -> str:
    """Render a clean 52-week trading range indicator."""
    if low is None or high is None or high <= low:
        return ""
    return f"""
    <div class="range-card">
      <div class="range-head">
        <span class="card-kicker" style="margin:0;">52-Week Trading Range</span>
        <span class="mono-muted">Spread: {((high - low) / low * 100):.1f}%</span>
      </div>
      <div class="range-values">
        <div>
          <div class="range-label">52W Low</div>
          <div class="range-num">${low:,.2f}</div>
        </div>
        <div class="range-bar-wrap">
          <div class="range-bar"></div>
        </div>
        <div style="text-align:right;">
          <div class="range-label">52W High</div>
          <div class="range-num">${high:,.2f}</div>
        </div>
      </div>
    </div>
    """
