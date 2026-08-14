"""Application configuration. Reads secrets from the environment."""
import os
from dotenv import load_dotenv

# Load variables from a local .env file (never committed to Git)
load_dotenv()

# --- Gemini (LLM) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MAX_DOC_TOKENS = int(os.getenv("MAX_DOC_TOKENS", "200000"))

# --- Supabase Postgres (database) ---
# Pooler connection string (port 6543) from Supabase → Connect → URI.
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Supabase Storage (PDF files) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")            # https://xxxx.supabase.co
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # service_role key (secret)
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "documents")


def require_api_key() -> str:
    """Return the Gemini API key or raise a clear error if it's missing."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return GEMINI_API_KEY


def require_database_url() -> str:
    """Return the database URL or raise a clear error if it's missing."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add your Supabase pooler connection string to .env."
        )
    return DATABASE_URL


def require_supabase() -> tuple[str, str]:
    """Return (url, service_key) or raise a clear error if either is missing."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env for file storage."
        )
    return SUPABASE_URL, SUPABASE_SERVICE_KEY