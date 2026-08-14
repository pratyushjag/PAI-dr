"""
Supabase Storage service.

Handles uploading the original PDF files to a Supabase Storage bucket,
so the app keeps the source file (not just the extracted text). Returns
the storage path, which we record in the documents table.
"""
import logging
import uuid

from supabase import create_client, Client

from config import require_supabase, SUPABASE_BUCKET

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    """Return the shared Supabase client, creating it on first call."""
    global _client
    if _client is None:
        url, service_key = require_supabase()
        _client = create_client(url, service_key)
        logger.info("Supabase storage client created.")
    return _client


def ensure_bucket() -> None:
    """
    Make sure the storage bucket exists. Safe to call on startup.
    Ignores the error if the bucket already exists.
    """
    client = get_client()
    try:
        buckets = client.storage.list_buckets()
        names = {b.name for b in buckets}
        if SUPABASE_BUCKET not in names:
            client.storage.create_bucket(SUPABASE_BUCKET)
            logger.info("Created storage bucket '%s'.", SUPABASE_BUCKET)
    except Exception as e:
        # Non-fatal: if we can't list/create, uploads will surface the real error.
        logger.warning("Could not verify storage bucket: %s", e)


def upload_pdf(filename: str, file_bytes: bytes) -> str:
    """
    Upload a PDF to Supabase Storage under a unique path.
    Returns the storage path (to save in the DB), or raises on failure.
    """
    # Prefix with a UUID so two files with the same name don't collide.
    path = f"{uuid.uuid4().hex}_{filename}"

    client = get_client()
    client.storage.from_(SUPABASE_BUCKET).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "application/pdf"},
    )
    logger.info("Uploaded '%s' to storage as '%s'.", filename, path)
    return path