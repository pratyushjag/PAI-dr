"""
Gemini LLM service.

Takes a document's text plus a user question and returns an answer.
Safeguards:
  1. Token guard    — refuse documents that would blow the token window.
  2. Trimmed history — only the last few Q&A turns are sent for context.
  3. Retry on failure — transient API errors (rate limits, blips) are
     retried a few times with a short backoff before giving up.
"""
import logging
import time
from google import genai
from google.genai import types

from config import require_api_key, GEMINI_MODEL, MAX_DOC_TOKENS

logger = logging.getLogger(__name__)

# How many recent Q&A turns to include as context.
HISTORY_TURNS_TO_SEND = 4

# Rough token estimate: ~4 characters per token for English text.
CHARS_PER_TOKEN = 4

# Retry settings for transient API failures.
MAX_ATTEMPTS = 3          # total tries before giving up
RETRY_BASE_DELAY = 1.0    # seconds; grows with each attempt (1s, 2s, ...)

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant that answers questions about a document. "
    "Base your answers only on the document text provided. "
    "If the answer is not in the document, say so plainly instead of guessing."
)


class DocumentTooLargeError(Exception):
    """Raised when a document exceeds the token guard limit."""


class LLMError(Exception):
    """Raised when the Gemini call fails after all retry attempts."""


def _estimate_tokens(text: str) -> int:
    """Cheap character-based token estimate."""
    return len(text) // CHARS_PER_TOKEN


def _build_prompt(document_text: str, question: str, history: list[dict]) -> str:
    """Assemble the full prompt: document, recent history, then the question."""
    parts = ["Here is the document:\n", document_text, "\n\n"]

    recent = history[-HISTORY_TURNS_TO_SEND:] if history else []
    if recent:
        parts.append("Earlier in this conversation:\n")
        for turn in recent:
            parts.append(f"Q: {turn['question']}\nA: {turn['answer']}\n")
        parts.append("\n")

    parts.append(f"Now answer this question:\n{question}")
    return "".join(parts)


def _call_gemini(prompt: str) -> str:
    """
    Make a single Gemini request and return the answer text.
    Raised exceptions are handled by the retry loop in answer_question.
    """
    client = genai.Client(api_key=require_api_key())
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )
    return (response.text or "").strip()


def answer_question(
    document_text: str,
    question: str,
    history: list[dict] | None = None,
) -> str:
    """
    Send the document + question to Gemini and return the answer text.

    Retries a few times on transient failures (rate limits, timeouts).
    Raises DocumentTooLargeError if the document exceeds the token guard,
    or LLMError if all attempts fail.
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

    # --- Retry loop: absorb transient API errors ---
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            answer = _call_gemini(prompt)
            if not answer:
                # An empty answer is treated as a failure worth retrying.
                raise ValueError("empty response from model")
            logger.info(
                "Answered question on attempt %d (~%d input tokens).",
                attempt, _estimate_tokens(prompt),
            )
            return answer
        except Exception as e:
            last_error = e
            logger.warning("Gemini call failed on attempt %d/%d: %s",
                           attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                # Wait a bit longer each time before retrying.
                time.sleep(RETRY_BASE_DELAY * attempt)

    # All attempts failed.
    logger.error("Gemini call failed after %d attempts: %s", MAX_ATTEMPTS, last_error)
    raise LLMError("The AI service could not answer right now. Please try again.")