import { useState } from "react";
import FileUpload from "./FileUpload";
import TextViewer from "./TextViewer";
import ChatBox from "./ChatBox";
import "./App.css";

export default function App() {
  // The one piece of shared state: the uploaded document (or null).
  // FileUpload sets it; TextViewer and ChatBox read from it.
  const [document, setDocument] = useState(null);

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Document Reader</h1>
        <p>Upload a PDF, read its text, and ask questions about it.</p>
      </header>

      <main className="app-main">
        <section className="app-upload">
          <FileUpload onUploaded={setDocument} />
        </section>

        <div className="app-columns">
          <section className="app-column">
            <h2 className="column-title">Document</h2>
            <TextViewer document={document} />
          </section>

          <section className="app-column">
            <h2 className="column-title">Ask</h2>
            <ChatBox documentId={document ? document.document_id : null} />
          </section>
        </div>
      </main>

      <footer className="app-footer">
        <span>Built with React, FastAPI, Gemini &amp; Supabase</span>
      </footer>
    </div>
  );
}