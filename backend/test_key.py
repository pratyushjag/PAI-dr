"""
Quick sanity check: confirms the Gemini API key is live and correctly
tied to the project. Run this once after setting up .env.

Usage:
    python test_key.py
"""
from google import genai
from config import require_api_key, GEMINI_MODEL


def main() -> None:
    api_key = require_api_key()  # raises a clear error if the key is missing
    client = genai.Client(api_key=api_key)

    print(f"Sending one test request to {GEMINI_MODEL} ...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Say hello in one word.",
    )

    print("\nSuccess. Gemini replied:")
    print(f"   {response.text.strip()}")
    print("\nThe key is live and the API is enabled. You're clear to build.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nTest failed:")
        print(f"   {type(e).__name__}: {e}")
        print("\nCommon fixes:")
        print("  - API_KEY_INVALID   -> the key was copied wrong; recopy it into .env")
        print("  - PERMISSION_DENIED -> enable the Gemini API on the project, wait a minute")
        print("  - Missing key       -> copy .env.example to .env and add your key")