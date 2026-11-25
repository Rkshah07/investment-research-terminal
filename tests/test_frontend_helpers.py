"""Unit tests for frontend formatting, SVG rendering, and export helpers."""

import json
import unittest

from frontend.charts import (
    render_52w_range_html,
    render_confidence_gauge_svg,
    render_radar_chart_svg,
    render_score_row_html,
)
from frontend.formatters import (
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


class TestFrontendHelpers(unittest.TestCase):
    def test_numeric_formatters(self):
        self.assertEqual(format_large_currency("3450000000000"), "$3.45T")
        self.assertEqual(format_large_currency("113270000000"), "$113.27B")
        self.assertEqual(format_large_currency("None"), "—")
        self.assertEqual(format_percent("0.556"), "55.6%")
        self.assertEqual(format_ratio("54.2", "x"), "54.20x")
        self.assertEqual(format_currency("2.58"), "$2.58")
        self.assertIsNone(safe_float("-"))

    def test_sample_reports_and_exports(self):
        samples = get_sample_reports()
        self.assertIn("NVIDIA", samples)
        self.assertIn("Tesla", samples)
        nvda = samples["NVIDIA"]
        self.assertGreater(compute_composite_score(nvda["analysis"]), 3.5)

        md = build_markdown_report(nvda)
        self.assertIn("Investment Research Report: NVIDIA (NVDA)", md)
        self.assertIn("VERDICT", md.upper())

        raw_json = build_json_report(nvda)
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["financials"]["symbol"], "NVDA")

    def test_svg_and_html_escapes_untrusted_text(self):
        gauge = render_confidence_gauge_svg(84, "INVEST")
        self.assertIn("<svg", gauge)
        self.assertIn("84%", gauge)

        radar = render_radar_chart_svg(
            [("Growth", 5), ("Profitability", 5), ("Valuation", 3), ("Moat", 5), ("Risk", 3)]
        )
        self.assertIn("<polygon", radar)

        row = render_score_row_html("Growth", "Trajectory", 4, "<script>alert(1)</script>")
        self.assertNotIn("<script>", row)
        self.assertIn("&lt;script&gt;", row)

        range_html = render_52w_range_html(66.25, 152.89)
        self.assertIn("$66.25", range_html)
        self.assertIn("$152.89", range_html)


if __name__ == "__main__":
    unittest.main()
