"""
Gemini LLM service.

Takes a document's text plus a user question and returns an answer.
Two safeguards keep us inside the free tier:
  1. Token guard  — refuse documents that would blow the token window.
  2. Trimmed history — only the last few Q&A turns are sent for context,
     not the entire chat, so each request stays lean.
"""
import logging
from google import genai
from google.genai import types

from config import require_api_key, GEMINI_MODEL, MAX_DOC_TOKENS

logger = logging.getLogger(__name__)

# How many recent Q&A turns to include as context. The full history still
# lives in the database and shows in the UI — this only limits what we
# send to the model per request.
HISTORY_TURNS_TO_SEND = 4

# Rough token estimate: ~4 characters per token for English text.
# Good enough for a guard; we're not billing on it.
CHARS_PER_TOKEN = 4

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant that answers questions about a document. "
    "Base your answers only on the document text provided. "
    "If the answer is not in the document, say so plainly instead of guessing."
)


class DocumentTooLargeError(Exception):
    """Raised when a document exceeds the token guard limit."""


class LLMError(Exception):
    """Raised when the Gemini call itself fails."""


def _estimate_tokens(text: str) -> int:
    """Cheap character-based token estimate."""
    return len(text) // CHARS_PER_TOKEN


def _build_prompt(document_text: str, question: str, history: list[dict]) -> str:
    """
    Assemble the full prompt: document, recent history, then the question.
    `history` is a list of {"question": ..., "answer": ...} dicts, oldest first.
    """
    parts = ["Here is the document:\n", document_text, "\n\n"]

    recent = history[-HISTORY_TURNS_TO_SEND:] if history else []
    if recent:
        parts.append("Earlier in this conversation:\n")
        for turn in recent:
            parts.append(f"Q: {turn['question']}\nA: {turn['answer']}\n")
        parts.append("\n")

    parts.append(f"Now answer this question:\n{question}")
    return "".join(parts)


def answer_question(
    document_text: str,
    question: str,
    history: list[dict] | None = None,
) -> str:
    """
    Send the document + question to Gemini and return the answer text.

    Raises DocumentTooLargeError if the document exceeds the token guard,
    or LLMError if the API call fails.
    """
    history = history or []

    # --- Token guard: stop oversized docs before they hit the API ---
    estimated = _estimate_tokens(document_text)
    if estimated > MAX_DOC_TOKENS:
        logger.warning(
            "Document too large: ~%d tokens (limit %d).", estimated, MAX_DOC_TOKENS
        )
        raise DocumentTooLargeError(
            f"This document is too large (~{estimated:,} tokens). "
            f"The limit is {MAX_DOC_TOKENS:,} tokens to stay within free-tier limits."
        )

    prompt = _build_prompt(document_text, question, history)

    try:
        client = genai.Client(api_key=require_api_key())
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
    except Exception as e:
        logger.error("Gemini call failed: %s", e)
        raise LLMError("The AI service could not answer right now.") from e

    answer = (response.text or "").strip()
    if not answer:
        raise LLMError("The AI service returned an empty answer.")

    logger.info("Answered question (~%d input tokens).", _estimate_tokens(prompt))
    return answer