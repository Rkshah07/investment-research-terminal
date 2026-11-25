"""
schemas.py
Pydantic models used to force structured (parseable) output from the LLM
at the synthesis and decision steps. Python port of the original
`src/graph/schemas.js` — the Zod schemas from the Node/LangChain.js version.

WHY this matters: without a schema, the LLM returns prose, and you end up
writing fragile regex/string-parsing to pull a "verdict" out of a paragraph.
LangChain's `.with_structured_output(schema)` makes the model return an
object matching this shape directly, which the Streamlit UI can render
without any parsing.

WHY EVERYTHING IS STILL FLAT (no nested models):
This constraint carries over unchanged from the JS version. Gemini's
structured-output API does not support nested object schemas — a nested
Pydantic model (e.g. `growth: GrowthModel`) compiles to JSON Schema using a
`$ref`/`$defs` reference, and Gemini's API rejects `$ref` outright with
"Unknown name '$ref': Cannot find field." This is a Gemini API limitation,
not a LangChain/Pydantic one, and it applies identically whether the schema
is built with Zod (JS) or Pydantic (Python). So instead of
`growth: {score, justification}`, we keep `growth_score` / `growth_justification`
as separate top-level fields — verbose, but it's what Gemini will accept.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    growthScore: int = Field(
        ..., ge=1, le=5, description="Growth dimension score, 1 (very weak) to 5 (very strong)"
    )
    growthJustification: str = Field(
        ..., description="One sentence citing specific data supporting the growth score"
    )

    profitabilityScore: int = Field(..., ge=1, le=5, description="Profitability dimension score, 1 to 5")
    profitabilityJustification: str = Field(
        ..., description="One sentence citing specific data supporting the profitability score"
    )

    valuationScore: int = Field(..., ge=1, le=5, description="Valuation dimension score, 1 to 5")
    valuationJustification: str = Field(
        ..., description="One sentence citing specific data supporting the valuation score"
    )

    moatScore: int = Field(..., ge=1, le=5, description="Moat/competitive advantage dimension score, 1 to 5")
    moatJustification: str = Field(
        ..., description="One sentence citing specific data supporting the moat score"
    )

    riskScore: int = Field(..., ge=1, le=5, description="Risk dimension score, 1 to 5")
    riskJustification: str = Field(
        ..., description="One sentence citing specific data supporting the risk score"
    )

    strengths: List[str] = Field(..., min_length=1, max_length=4, description="2-4 short bullet points on key strengths")
    risks: List[str] = Field(..., min_length=1, max_length=4, description="2-4 short bullet points on key risks")


class Verdict(BaseModel):
    verdict: Literal["INVEST", "PASS", "WATCH"]
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str = Field(..., description="3-5 sentences explaining the call")
    whatWouldChangeMyMind: str = Field(..., description="1-3 sentences on what data would flip this verdict")
