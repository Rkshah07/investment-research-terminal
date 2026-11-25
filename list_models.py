"""
list_models.py
Query Google's Generative Language API to list model names your API key
can use. Helpful when a hardcoded model name in `cli.py`/`app.py` returns
a 404. Python port of `src/list-models.js`.

Usage:
    python list_models.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY is not set. Fill in your .env file first.")
        sys.exit(1)

    res = httpx.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=15.0,
    )

    if res.status_code >= 400:
        print(f"Failed to list models: {res.status_code} {res.reason_phrase}")
        print(res.text)
        sys.exit(1)

    data = res.json()
    usable = [
        m for m in data.get("models", []) if "generateContent" in (m.get("supportedGenerationMethods") or [])
    ]

    print("\nModels your key can use with generateContent:\n")
    for m in usable:
        # m["name"] looks like "models/gemini-2.5-flash" — strip the
        # "models/" prefix, since that's the bare string you pass into
        # ChatGoogleGenerativeAI(model=...)
        print(f"  {m['name'].replace('models/', '')}")

    print("\nCopy one of the names above (without 'models/') into cli.py / app.py as the model value.\n")


if __name__ == "__main__":
    main()
