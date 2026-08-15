// Shows the extracted text from the uploaded PDF.
// `document` is the backend's upload response, or null before any upload.
export default function TextViewer({ document }) {
  if (!document) {
    return (
      <div className="viewer viewer-empty">
        <p>Upload a PDF to see its extracted text here.</p>
      </div>
    );
  }

  // The backend tells us how it read the text: "text" (normal) or "ocr" (scanned).
  const readVia =
    document.method === "ocr"
      ? "Read via OCR (scanned document)"
      : "Extracted directly from the PDF";

  return (
    <div className="viewer">
      <div className="viewer-header">
        <span className="viewer-filename">{document.filename}</span>
        <span className="viewer-meta">
          {document.char_count.toLocaleString()} characters · {readVia}
        </span>
      </div>
      <pre className="viewer-text">{document.text}</pre>
    </div>
  );
}