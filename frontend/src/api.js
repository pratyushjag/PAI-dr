// All communication with the backend lives here, in one place.
// The backend URL comes from an environment variable so the same code
// works locally and when deployed (Vercel/Railway) with no changes.
// Vite exposes env vars prefixed with VITE_ on import.meta.env.
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// A small helper: turn a failed response into a useful Error.
// The backend sends { "detail": "..." } on errors, so we surface that.
async function handleResponse(response) {
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) message = data.detail;
    } catch {
      // response had no JSON body; keep the generic message
    }
    throw new Error(message);
  }
  return response.json();
}

// 1. Upload a PDF. Returns { document_id, filename, method, text, char_count }.
export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

// 2. Ask a question about a document. Returns { answer }.
export async function askQuestion(documentId, question) {
  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, question }),
  });
  return handleResponse(response);
}

// 3. Get the chat history for a document.
// Returns { document_id, filename, messages: [{ question, answer, created_at }] }.
export async function getHistory(documentId) {
  const response = await fetch(`${API_BASE}/history/${documentId}`);
  return handleResponse(response);
}