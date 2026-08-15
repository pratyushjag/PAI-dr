import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion } from "./api";

// The chat panel. Enabled once a document is uploaded (documentId is set).
// Keeps the running list of question/answer pairs for this document.
export default function ChatBox({ documentId }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]); // { question, answer } pairs
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    setError("");
    setIsAsking(true);
    setQuestion(""); // clear the input right away

    try {
      const result = await askQuestion(documentId, trimmed);
      setMessages((prev) => [...prev, { question: trimmed, answer: result.answer }]);
    } catch (err) {
      setError(err.message || "Could not get an answer. Please try again.");
      setQuestion(trimmed); // put the question back so it isn't lost
    } finally {
      setIsAsking(false);
    }
  }

  // Send on Enter (but allow Shift+Enter for a newline).
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }

  // Before a document is uploaded, invite the user to upload first.
  if (!documentId) {
    return (
      <div className="chat chat-empty">
        <p>Upload a document to start asking questions.</p>
      </div>
    );
  }

  return (
    <div className="chat">
      <div className="chat-history">
        {messages.length === 0 && (
          <p className="chat-hint">Ask anything about the document above.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className="chat-turn">
            <p className="chat-question">{m.question}</p>
            <div className="chat-answer">
              <ReactMarkdown>{m.answer}</ReactMarkdown>
            </div>
          </div>
        ))}
        {isAsking && <p className="chat-thinking">Thinking…</p>}
      </div>

      {error && <p className="chat-error">{error}</p>}

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question…"
          rows={2}
          disabled={isAsking}
        />
        <button
          className="chat-send"
          onClick={handleSubmit}
          disabled={isAsking || !question.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}