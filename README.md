# AI-Powered Document Reader

A full-stack web application that extracts text from uploaded PDF documents and answers
questions about them using a large language model. Upload a PDF, read its extracted text,
and have a grounded conversation about its contents.
The name **PAI-dr** stands for "Powered with AI — Document Reader."

## Live Application

| Resource | URL |
|---|---|
| **Frontend (web app)** | https://pai-dr.vercel.app |
| **Backend API** | https://pai-dr-production.up.railway.app |
| **API Docs (Swagger)** | https://pai-dr-production.up.railway.app/docs |
| **Source (GitHub)** | https://github.com/pratyushjag/PAI-dr |

> The app is mobile-responsive — the live URL works equally well on a phone browser.

---

## Demo

A short walkthrough of the app: https://drive.google.com/file/d/1H7WaoSo-i5JFYyvG8jh0g4R98QAivvVu/view?usp=drivesdk

---

## Tech Stack

| Layer | Technology | Hosted on |
|---|---|---|
| Frontend | React (Vite) | Vercel |
| Backend | Python, FastAPI | Railway |
| Database | PostgreSQL | Supabase |
| File storage | Supabase Storage | Supabase |
| LLM | Google Gemini (`gemini-flash-lite-latest`) | — |
| PDF extraction | PyMuPDF | — |
| OCR fallback | Tesseract (via pytesseract) | — |

---

## Architecture

The application is split into a React single-page frontend and a FastAPI backend, with
Supabase providing both the database and object storage. The frontend never talks to the
database or the LLM directly — all of that goes through the backend API, which keeps
credentials server-side and the architecture clean.

```
                                             ┌────────────────────┐
                                             │   Google Gemini    │
                                             │   (LLM Q&A)         │
                                             └─────────▲──────────┘
                                                       │
  ┌──────────────┐   HTTPS    ┌─────────────────────────────────┐        ┌──────────────────┐
  │   Browser    │ ─────────► │        FastAPI Backend           │ ─────► │  Supabase         │
  │ (React SPA   │            │        (Railway)                 │        │  - PostgreSQL     │
  │  on Vercel)  │ ◄───────── │   /upload  /ask  /history        │ ◄───── │  - Storage bucket │
  └──────────────┘            └─────────────────────────────────┘        └──────────────────┘
```

**Request flow for asking a question about a document:**

1. The user uploads a PDF in the browser. The frontend sends it to `POST /upload`.
2. The backend extracts the text (PyMuPDF; Tesseract OCR fallback for scanned PDFs),
   stores the original file in Supabase Storage, and saves the extracted text plus
   metadata as a row in PostgreSQL. It returns a `document_id` and the text.
3. The frontend displays the text and enables the chat.
4. The user asks a question. The frontend sends it with the `document_id` to `POST /ask`.
5. The backend loads the document text and recent chat history, sends them to Gemini,
   stores the resulting Q&A pair, and returns the answer.
6. The frontend renders the answer (with markdown formatting).

---

## Project Structure

```
PAI-dr/
├── backend/
│   ├── main.py                  # FastAPI app: routes, CORS, request/response models
│   ├── config.py                # Reads all settings/secrets from environment variables
│   ├── database.py              # PostgreSQL access (psycopg) — documents & messages tables
│   ├── services/
│   │   ├── pdf_service.py       # PDF text extraction + gated OCR fallback
│   │   ├── llm_service.py       # Gemini calls: token guard, trimmed history, retry logic
│   │   └── storage_service.py   # Uploads original PDFs to Supabase Storage
│   ├── test_key.py              # Standalone script to verify the Gemini API key works
│   ├── requirements.txt         # Python dependencies (pinned)
│   └── .env.example             # Template for the required environment variables
│
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component — layout + shared document state
    │   ├── api.js              # All backend calls; backend URL from an env var
    │   ├── FileUpload.jsx      # PDF picker, upload, loading & error states
    │   ├── TextViewer.jsx      # Displays extracted text + how it was read
    │   ├── ChatBox.jsx         # Q&A interface with markdown rendering
    │   ├── App.css             # Application styling (responsive)
    │   └── index.css           # Base/reset styles
    ├── package.json
    └── index.html
```

### What each backend file does

- **`main.py`** — Defines the FastAPI application and its four endpoints (`/health`,
  `/upload`, `/ask`, `/history`). Configures CORS (so the Vercel frontend may call the
  API), sets up logging, and defines the Pydantic request/response models that also
  generate the Swagger docs. On startup it ensures the database tables and the storage
  bucket exist.
- **`config.py`** — The single place that reads configuration. Every secret and setting
  (API keys, database URL, model name, limits) comes from environment variables, so no
  credentials are ever hard-coded. Provides small helpers that raise clear errors if a
  required value is missing.
- **`database.py`** — All PostgreSQL access, using `psycopg` with a connection pool.
  Creates two tables (`documents`, `messages`), and exposes functions to save/fetch
  documents and to save/fetch chat history.
- **`services/pdf_service.py`** — Extracts text from an uploaded PDF using PyMuPDF. If a
  PDF yields no real text (the signal of a scanned document), it falls back to Tesseract
  OCR. Raises a clear error for invalid/unreadable files instead of crashing.
- **`services/llm_service.py`** — Talks to Google Gemini. Builds the prompt from the
  document text plus the recent chat history, guards against oversized documents (token
  limit), and retries transient API failures with a short backoff before giving up.
- **`services/storage_service.py`** — Uploads the original PDF file to a Supabase Storage
  bucket and returns the stored path, which is recorded alongside the document.
- **`test_key.py`** — A quick sanity-check script that sends one request to Gemini to
  confirm the configured API key is live before running the full app.

### What each frontend file does

- **`App.jsx`** — The root component. Holds the single piece of shared state (the uploaded
  document) and composes the upload box, text viewer, and chat panel on one page.
- **`api.js`** — The one module that communicates with the backend. The backend URL is
  read from `VITE_API_BASE_URL`, so the same code works locally and in production.
- **`FileUpload.jsx`** — The upload control. Handles choosing a PDF, the upload request,
  and the loading/error states.
- **`TextViewer.jsx`** — Displays the extracted text and notes how it was read (direct
  extraction vs. OCR).
- **`ChatBox.jsx`** — The question-and-answer interface. Keeps the visible conversation
  history and renders answers as formatted markdown.

---

## Requirements Coverage

Every functional requirement from the assignment is implemented:

| # | Requirement | How it's met |
|---|---|---|
| 1 | Upload PDF documents | `POST /upload` endpoint + `FileUpload` component |
| 2 | Extract text from PDFs | `pdf_service.py` (PyMuPDF) |
| 3 | Display extracted text | `TextViewer` component |
| 4 | Ask questions about the document | `POST /ask` + `ChatBox` component |
| 5 | Generate answers using an LLM | `llm_service.py` (Google Gemini) |
| 6 | Maintain chat history per document | `messages` table + `/history` endpoint |
| 7 | Gracefully handle invalid/scanned PDFs (OCR bonus) | Invalid files return clear errors; scanned PDFs trigger the OCR fallback path (see note below) |
| 8 | Meaningful error handling and logging | Proper HTTP status codes with clear messages throughout; structured logging in every layer |

**Bonus — Deployment:** the full application is deployed across three cloud platforms
(Vercel, Railway, Supabase).

**Note on Gemini (requirement 5):** The app uses Gemini's free tier; rapid repeated testing may hit rate limits, which reset automatically.

**Note on OCR (requirement 7):** Invalid and scanned PDFs are both handled gracefully —
invalid files are rejected with a clear message, and scanned PDFs are detected and routed
through the OCR fallback (Tesseract). The OCR code path is implemented in `pdf_service.py`;
Tesseract must be present in the runtime environment for scanned-text extraction to fully
activate.

**Note on extraction scope:** Extraction covers the text content of PDFs. Embedded figures,
diagrams, and images are not processed as text, so questions about purely visual elements
(e.g. "what does Figure 3 show") fall outside the app's scope.


---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key (free tier) — https://aistudio.google.com/apikey
- A Supabase project (free tier) — https://supabase.com
- *(Optional, for OCR on scanned PDFs)* Tesseract OCR engine — see note below
### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) For OCR on scanned PDFs, install the Tesseract engine:
#   macOS:         brew install tesseract
#   Ubuntu/Debian: sudo apt install tesseract-ocr
#   Windows:       download from https://github.com/UB-Mannheim/tesseract/wiki
# Without Tesseract, scanned PDFs are still handled gracefully with a clear message.

# Create your environment file from the template and fill in your values
cp .env.example .env
#   (edit .env — see "Environment Variables" below)

# (Optional) verify your Gemini key works
python test_key.py

# Run the backend
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The app runs at `http://localhost:5173`.

**Backend URL:** by default the frontend talks to `http://localhost:8000` (the local
backend), so no configuration is needed for local development. To point it elsewhere,
create a `frontend/.env.local` file with:

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Sample Documents

Sample PDFs for testing are provided in the [`sample_documents/`](sample_documents/) folder:

- **Text PDFs** — demonstrate standard text extraction.
- **Scanned PDF** — demonstrates graceful handling of image-based documents
  (the scanned-PDF detection and fallback path).

## Environment Variables

The backend reads all configuration from environment variables (locally via `.env`, and in
production via the hosting platform's variable settings). A template is provided in
`backend/.env.example`.

| Variable | Description | Example |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (secret) | `AIza...` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-flash-lite-latest` |
| `MAX_DOC_TOKENS` | Max document size sent to the model | `200000` |
| `DATABASE_URL` | Supabase PostgreSQL connection string (secret) | `postgresql://postgres.xxx:...@...pooler.supabase.com:6543/postgres` |
| `SUPABASE_URL` | Supabase project URL | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service key (secret) | `sb_secret_...` |
| `SUPABASE_BUCKET` | Storage bucket name for PDFs | `documents` |

The frontend uses one variable:

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the backend API | `https://pai-dr-production.up.railway.app` |

> Secrets are never committed to the repository. `.env` is gitignored; only `.env.example`
> (with placeholder values) is tracked.

---

## Deployment

The application is deployed across three platforms, all connected via environment variables.

### Database & Storage — Supabase

A Supabase project provides both the PostgreSQL database and the Storage bucket for PDF
files. The backend creates its tables and bucket automatically on first startup.

### Backend — Railway

The FastAPI backend is deployed on Railway from the GitHub repository:

- **Root directory:** `backend`
- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** the seven backend variables listed above are set in Railway's
  Variables settings.

Railway rebuilds automatically on each push to the `master` branch.

### Frontend — Vercel

The React frontend is deployed on Vercel from the same repository:

- **Root directory:** `frontend`
- **Framework preset:** Vite (auto-detected)
- **Environment variable:** `VITE_API_BASE_URL` is set to the Railway backend URL.

Vercel rebuilds automatically on each push.

### Connecting the two

The frontend calls the backend using `VITE_API_BASE_URL`. The backend's CORS configuration
explicitly allows the deployed frontend origin so the browser permits those cross-origin
requests.

---

## API Reference

Interactive documentation is available at `/docs` (Swagger UI) on the backend.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status": "ok"}` |
| `POST` | `/upload` | Upload a PDF; returns extracted text, a `document_id`, and metadata |
| `POST` | `/ask` | Ask a question about a document (`document_id` + `question`); returns the answer |
| `GET` | `/history/{document_id}` | Returns the full chat history for a document |

---

## Notable Design Decisions

- **Environment-driven configuration.** Both the backend and frontend read all
  environment-specific values (backend URL, credentials, model) from environment
  variables, so the exact same code runs locally and in production with no changes.
- **Clean separation of concerns.** The frontend has a single API module; the backend
  splits PDF handling, LLM calls, storage, and database access into focused services.
- **Cost-aware LLM usage.** A token guard prevents oversized documents from exceeding
  free-tier limits, and only the recent chat history (not the entire conversation) is sent
  with each request.
- **Resilience.** Transient LLM failures are automatically retried with a short backoff, so
  a momentary API blip doesn't surface as an error to the user.
- **Graceful degradation.** Invalid and scanned PDFs produce clear, specific messages
  rather than crashes.

  ## Screenshots

**Initial interface (desktop)**

![Initial UI](screenshots/pc_upload_ui_1.png)

**Document uploaded — text extracted (desktop)**

![Document uploaded](screenshots/pc_upload_ui_2.png)

**Graceful handling of a scanned PDF (desktop)**

![Scanned PDF handling](screenshots/pc_upload_ui_ocr.png)

**Mobile — document uploaded and text extracted**

![Mobile upload](screenshots/mobile_upload.jpeg)

**Mobile — asking a question about the document**

![Mobile chat](screenshots/mobile_chat.jpeg)