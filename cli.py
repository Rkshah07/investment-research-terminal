"""
cli.py
Small CLI helper to run the full agent graph from the terminal. Python
port of `src/run.js`. Use this to iterate on prompts/rubric changes without
the Streamlit frontend.

Example:
    python cli.py "Tesla"
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.graph.graph import build_investment_research_graph

load_dotenv()


async def main():
    if len(sys.argv) < 2:
        print('Usage: python cli.py "<company name>"')
        sys.exit(1)

    company_name = sys.argv[1]

    if not os.environ.get("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY is not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)

    # Note on model choice: lighter/cheaper models can produce trivial or
    # incorrect justifications for this structured task (see README). If
    # you get a 404 for the model name, run `python list_models.py` to see
    # which models your key supports. Transient 503s are usually
    # temporary — retry.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,  # low temperature: consistent, grounded analysis, not creativity
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )

    app = build_investment_research_graph(llm)

    print(f"\nResearching: {company_name}\n{'=' * 50}")
    print("(streaming progress — each line below appears as that step finishes)\n")

    final_state = {"companyName": company_name, "trace": [], "errors": []}

    # Use .astream() so progress prints as each node finishes instead of
    # waiting for the entire graph to complete. Each chunk contains partial
    # state updates keyed by node name.
    async for chunk in app.astream({"companyName": company_name}):
        for node_name, update in chunk.items():
            for line in update.get("trace", []) or []:
                print(f"[{node_name}] {line}")
            final_state = {
                **final_state,
                **update,
                "trace": final_state["trace"] + (update.get("trace") or []),
                "errors": final_state["errors"] + (update.get("errors") or []),
            }

    if final_state["errors"]:
        print("\n--- ERRORS (non-fatal) ---")
        for e in final_state["errors"]:
            print(f"  ! {e}")

    print("\n--- ANALYSIS ---")
    print(json.dumps(final_state.get("analysis"), indent=2))

    print("\n--- VERDICT ---")
    print(json.dumps(final_state.get("verdict"), indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)
