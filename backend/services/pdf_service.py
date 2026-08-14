"""
PDF text extraction.

Primary path: PyMuPDF (fast, accurate for normal text-based PDFs).
Fallback path: Tesseract OCR — only runs when PyMuPDF finds no real text,
which is the signal that the PDF is scanned (images of text, not text).
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# If extracted text is shorter than this, we treat the PDF as "no real text"
# and fall back to OCR. A few stray characters don't count as a real extract.
MIN_TEXT_LENGTH = 20


class PDFExtractionError(Exception):
    """Raised when a file can't be opened or read as a PDF at all."""


def extract_text(file_bytes: bytes) -> tuple[str, str]:
    """
    Extract text from a PDF.

    Returns a tuple: (extracted_text, method_used).
    method_used is "text" for normal PDFs or "ocr" for scanned ones —
    useful for logging and for telling the user how the text was read.

    Raises PDFExtractionError if the bytes aren't a readable PDF.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        logger.error("Could not open file as PDF: %s", e)
        raise PDFExtractionError("The uploaded file is not a valid PDF.") from e

    # --- Primary path: direct text extraction ---
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    text = "\n".join(text_parts).strip()

    if len(text) >= MIN_TEXT_LENGTH:
        logger.info("Extracted %d characters via direct text.", len(text))
        doc.close()
        return text, "text"

    # --- Fallback path: OCR (scanned PDF) ---
    logger.info("Little/no text found; falling back to OCR.")
    ocr_parts = []
    try:
        for page in doc:
            # Render the page to an image, then OCR it.
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_parts.append(pytesseract.image_to_string(img))
    except Exception as e:
        doc.close()
        logger.error("OCR failed: %s", e)
        raise PDFExtractionError(
            "This looks like a scanned PDF, but OCR failed to read it."
        ) from e

    doc.close()
    ocr_text = "\n".join(ocr_parts).strip()

    if not ocr_text:
        raise PDFExtractionError(
            "No text could be extracted from this PDF, even with OCR."
        )

    logger.info("Extracted %d characters via OCR.", len(ocr_text))
    return ocr_text, "ocr"