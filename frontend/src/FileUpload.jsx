import { useState } from "react";
import { uploadPdf } from "./api";

// The upload box. When a PDF is chosen and uploaded, it calls onUploaded
// with the backend's response (document_id, text, etc.) so the parent
// can show the text and enable the chat.
export default function FileUpload({ onUploaded }) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");

  async function handleFileChange(event) {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setError("");
    setIsUploading(true);

    try {
      const result = await uploadPdf(file);
      onUploaded(result); // hand the result up to the parent
    } catch (err) {
      setError(err.message || "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="upload">
      <label className="upload-label">
        {isUploading ? "Processing…" : "Choose a PDF to upload"}
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={isUploading}
          hidden
        />
      </label>

      {fileName && !error && (
        <p className="upload-filename">{fileName}</p>
      )}

      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}