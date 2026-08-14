"""
Supabase Postgres persistence.

Two tables:
  documents  — one row per uploaded PDF (extracted text + metadata + storage path)
  messages   — chat history, each row a question/answer pair tied to a document

Uses psycopg (v3) with a connection pool. The connection string is the
Supabase pooler URI (port 6543), read from config.DATABASE_URL.
"""
import logging
from datetime import datetime, timezone

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from config import require_database_url

logger = logging.getLogger(__name__)

# A single shared pool for the app. Opened lazily on first use.
# The pooler already pools on Supabase's side; a small local pool is plenty.
_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=require_database_url(),
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row},
            open=True,
        )
        logger.info("Database connection pool created.")
    return _pool


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with get_pool().connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id           BIGSERIAL PRIMARY KEY,
                filename     TEXT NOT NULL,
                text         TEXT NOT NULL,
                method       TEXT NOT NULL,        -- "text" or "ocr"
                storage_path TEXT,                 -- path in Supabase Storage
                created_at   TIMESTAMPTZ NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id           BIGSERIAL PRIMARY KEY,
                document_id  BIGINT NOT NULL REFERENCES documents (id),
                question     TEXT NOT NULL,
                answer       TEXT NOT NULL,
                created_at   TIMESTAMPTZ NOT NULL
            );
            """
        )
        conn.commit()
    logger.info("Database initialized (tables ready).")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def save_document(filename: str, text: str, method: str, storage_path: str | None) -> int:
    """Store an uploaded document's extracted text. Returns its new ID."""
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO documents (filename, text, method, storage_path, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (filename, text, method, storage_path, _now()),
        ).fetchone()
        conn.commit()
        return row["id"]


def get_document(document_id: int) -> dict | None:
    """Fetch a document by ID, or None if it doesn't exist."""
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = %s", (document_id,)
        ).fetchone()
        return dict(row) if row else None


def save_message(document_id: int, question: str, answer: str) -> None:
    """Store one Q&A pair for a document."""
    with get_pool().connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (document_id, question, answer, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (document_id, question, answer, _now()),
        )
        conn.commit()


def get_history(document_id: int) -> list[dict]:
    """Return all Q&A pairs for a document, oldest first."""
    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT question, answer, created_at FROM messages
            WHERE document_id = %s ORDER BY id ASC
            """,
            (document_id,),
        ).fetchall()
        return [dict(r) for r in rows]