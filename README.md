# Sprinto AI Resume Screener

An AI-powered resume screening and ranking platform built for Sprinto's Implementations Intern assignment. Upload resumes against a job description and receive structured, ranked candidate evaluations powered by Google Gemini — with semantic search, bias-reduction tooling, and a production-ready full-stack architecture.

**Live Demo:** [Add your Vercel URL here]
**Backend API Docs:** [Add your Railway URL]/docs

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Deployment](#deployment)

---

## Features

### Resume Parsing

- **Multi-format support** — PDF, DOCX, DOC, RTF, TXT, Markdown, HTML, XML, images (PNG, JPG, TIFF, HEIC, BMP), and email formats (EML, MSG).
- **Unstructured.io API** — Primary parser using `hi_res` strategy for PDFs and images, with parallel page splitting and automatic table extraction.
- **Automatic fallback** — `pdfplumber` for PDFs and `python-docx` for DOCX when Unstructured.io is unavailable or returns insufficient text.
- **Parse report** — Every resume receives a confidence score, the method used, sections detected, character count, and any warnings.
- **10 MB file size limit** with descriptive error messaging.

### AI-Powered Scoring

- **Gemini 2.0 Flash** scores each resume against the job description across multiple dimensions (skills match, experience relevance, education, communication, etc.).
- **Overall score** (0–10) with a structured recommendation tier: `Strongly Recommend`, `Recommend`, `Maybe`, or `Do Not Advance`.
- **Confidence level** (`high`, `medium`, `low`) based on parse quality and available information.
- **Recruiter summary** — A concise plain-English paragraph generated per candidate.
- **Strengths and concerns** — Bulleted evaluation points surfaced directly from the model.
- **Suggested interview questions** — Tailored questions generated per candidate to aid in structured interviews.
- **Score critique** — A self-critique pass that checks scoring consistency and flags edge cases, improving calibration.
- **RAG-augmented scoring** — For each JD requirement, the most relevant resume passage is retrieved via pgvector similarity search and injected into the scoring prompt for grounded, evidence-backed evaluation.

### Candidate Intelligence

- **AI authorship detection** — Flags resumes exhibiting signals of AI-generated prose.
- **Contradiction detection** — Flags logical inconsistencies within a resume (e.g., overlapping employment date ranges, mismatched titles).
- **Configurable field extraction** — Gemini extracts structured fields from each resume: name, email, phone, current title, years of experience, skills, education, and summary. All fields are fully customisable per role.
- **Batch re-extraction** — Re-run field extraction and scoring on all resumes in a role after updating the field configuration.

### Job Description Tools

- **JD Quality Analyzer** — Analyzes the job description for vague requirements, missing must-haves, bias signals, and overall quality. Returns a flagged quality report with actionable improvement suggestions.
- **Live JD preview** — Analyze JD quality before creating or saving a role.
- **JD decomposition** — Breaks the job description into structured requirements that anchor all scoring and RAG retrieval.
- **Inline JD editor** — Edit and re-analyze the JD from the role settings page without leaving the UI.

### Search & Discovery

- **Semantic search** — Natural language search across all candidates in a role, powered by pgvector cosine similarity over 3072-dimensional Gemini embeddings. Returns ranked results with similarity percentages.
- **Similar candidate finder** — For any candidate, surface the most similar profiles within the same role using averaged chunk embeddings.
- **Multi-role comparison** — Score a single resume against multiple roles simultaneously and compare results.

### Bias Reduction

- **Blind Mode** — Per-role toggle that strips PII (name, email, phone) from the AI scoring prompt. The UI shows candidates as "Candidate #N" when enabled, removing all identifying information from the review workflow.

### Role & Candidate Management

- **Role CRUD** — Create, list, update, and delete hiring roles with title and job description.
- **Duplicate detection** — SHA-256 file hash prevents the same file from being processed twice for the same role. Returns an instant `duplicate` status without consuming AI API quota.
- **Candidate deletion** — Remove a candidate along with their stored file, score, and all embedding chunks.
- **Supabase file storage** — Uploaded resume files are persisted to Supabase Storage (best-effort; the pipeline continues if storage is unavailable).
- **Demo seed data** — `POST /api/seed` loads a curated multi-role showcase dataset for quick demonstrations.

### Pipeline & Infrastructure

- **Async background pipeline** — Parsing, extraction, embedding, and scoring all run as FastAPI background tasks. The UI polls for status updates every 3–5 seconds.
- **Processing status tracking** — Each resume progresses through `pending → parsing → extracting → scoring → scored` (or `error` / `duplicate`) with live display.
- **Gemini rate limiting** — All API calls are serialized through an asyncio semaphore with a 4-second minimum interval and exponential backoff on `429` errors, designed to stay within the 15 RPM free tier.
- **pgvector embeddings** — 3072-dimensional vectors stored in PostgreSQL for RAG scoring, semantic search, and similar-candidate discovery.
- **Cascade deletes** — Deleting a role removes all associated resumes, scores, and embedding chunks atomically.

---

## Architecture

```
Browser (Next.js 14)
       │
       │  REST / JSON  (SWR polling)
       ▼
FastAPI  (Python 3.11)
  ├── /api/roles     — CRUD, JD analysis, config, batch-reparse
  └── /api/resumes   — Upload, list, search, similar, multi-role

Background Pipeline  (per resume upload)
  1. parse_resume      →  Unstructured.io API  (fallback: pdfplumber / python-docx)
  2. extract_fields    →  Gemini 2.0 Flash      (structured JSON extraction)
  3. embed_chunks      →  Gemini Embedding-001  (3072-dim vectors → pgvector)
  4. rag_context       →  pgvector similarity   (retrieve relevant passages per JD requirement)
  5. score_resume      →  Gemini 2.0 Flash      (dimensional scoring + critique)
  6. store_results     →  PostgreSQL

PostgreSQL  (Railway)
  ├── roles
  ├── resumes
  ├── scores
  └── resume_chunks   (pgvector Vector(3072))

Supabase Storage  (file blobs, best-effort)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui, SWR |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), asyncpg, Pydantic v2 |
| AI / LLM | Google Gemini 2.0 Flash, Gemini Embedding-001 |
| Document Parsing | Unstructured.io API, pdfplumber, python-docx |
| Database | PostgreSQL 15+ with pgvector |
| File Storage | Supabase Storage |
| Deployment | Railway (backend + DB), Vercel (frontend) |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app, CORS middleware, lifespan hook
│   │   ├── config.py                   # Pydantic settings loaded from environment
│   │   ├── database.py                 # Async SQLAlchemy engine and session factory
│   │   ├── seed.py                     # Demo dataset loader
│   │   ├── models/
│   │   │   ├── role.py                 # Role model + default extraction config
│   │   │   ├── resume.py               # Resume model (status, hashes, extracted fields)
│   │   │   └── score.py                # Score + ResumeChunk (pgvector) models
│   │   ├── schemas/                    # Pydantic v2 request/response schemas
│   │   ├── routers/
│   │   │   ├── roles.py                # Role endpoints + JD analysis + batch-reparse
│   │   │   └── resumes.py              # Resume endpoints + semantic search + similar
│   │   ├── services/
│   │   │   ├── pipeline.py             # Orchestrates the full parse → score pipeline
│   │   │   ├── parser.py               # Unstructured.io + pdfplumber/docx fallback
│   │   │   ├── gemini.py               # Gemini LLM + embedding client (rate-limited)
│   │   │   ├── rag.py                  # pgvector retrieval for RAG context injection
│   │   │   ├── jd_analyzer.py          # JD quality analysis and decomposition
│   │   │   ├── multi_role.py           # Score one resume against N roles
│   │   │   ├── duplicate.py            # SHA-256 file hash deduplication
│   │   │   └── storage.py              # Supabase Storage upload and delete
│   │   └── prompts/                    # Prompt templates for all Gemini calls
│   ├── Dockerfile
│   ├── Procfile
│   ├── railway.toml
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx                # Home: role list + create role form
    │   │   ├── layout.tsx              # Root layout, Geist fonts, Toaster
    │   │   └── roles/[id]/
    │   │       ├── page.tsx            # Role detail: upload, ranked candidates, search
    │   │       ├── settings/page.tsx   # JD editor, blind mode, extraction config
    │   │       └── candidates/[cid]/   # Candidate detail view
    │   ├── components/
    │   │   ├── layout/                 # Header
    │   │   ├── roles/                  # JDQualityNotice, role creation form
    │   │   ├── resumes/                # UploadZone (drag-and-drop), StatusBadge
    │   │   └── scores/                 # ScoreCard with dimensional score bars
    │   ├── hooks/
    │   │   └── use-polling.ts          # SWR-based polling hook
    │   └── lib/
    │       └── api.ts                  # Typed API client for all backend calls
    ├── next.config.mjs
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with the `pgvector` extension enabled
- Google Gemini API key — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- (Optional) Unstructured.io API key — improves PDF and image-based resume parsing
- (Optional) Supabase project — for persistent resume file storage

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env — set DATABASE_URL and GEMINI_API_KEY at minimum

# Enable pgvector (run once against your PostgreSQL database)
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Start the development server
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

npm install

# Set the backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

- App: `http://localhost:3000`

### Load Demo Data

With both services running, seed sample roles and candidates:

```bash
curl -X POST http://localhost:8000/api/seed
```

> **Warning:** This replaces all existing roles and candidates.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL async connection string (`postgresql+asyncpg://user:pass@host:5432/db`) |
| `DATABASE_SSL` | No | `auto` (default — no SSL locally, require SSL on remote), `require`, or `disable` |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `UNSTRUCTURED_API_KEY` | No | Unstructured.io API key (falls back to pdfplumber when absent) |
| `SUPABASE_URL` | No | Supabase project URL (`https://xxx.supabase.co`) |
| `SUPABASE_KEY` | No | Supabase anon or service role key |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `http://localhost:3000`) |
| `ENVIRONMENT` | No | `development` or `production` |

### Frontend

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL (default: `http://localhost:8000`) |

---

## API Reference

### Roles

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/roles` | Create a new role |
| `GET` | `/api/roles` | List all active roles with resume counts and average score |
| `GET` | `/api/roles/{id}` | Get a role with full stats |
| `PUT` | `/api/roles/{id}` | Update role title, JD text, or blind mode |
| `DELETE` | `/api/roles/{id}` | Delete role and all data (cascade) |
| `POST` | `/api/roles/{id}/analyze-jd` | Run JD quality analysis and decomposition |
| `POST` | `/api/roles/analyze-jd-preview` | Preview JD quality without saving |
| `GET` | `/api/roles/{id}/config` | Get the extraction field configuration |
| `PUT` | `/api/roles/{id}/config` | Update extraction fields (auto-increments version) |
| `POST` | `/api/roles/{id}/batch-reparse` | Re-run extraction and scoring on all scored resumes |

### Resumes

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/roles/{id}/resumes` | Upload a resume file (starts async pipeline) |
| `GET` | `/api/roles/{id}/resumes` | List all resumes for a role, ordered by upload time |
| `GET` | `/api/resumes/{id}` | Get a single resume with full score data |
| `DELETE` | `/api/resumes/{id}` | Delete resume, score, chunks, and stored file |
| `GET` | `/api/roles/{id}/search?q={query}&limit={n}` | Semantic search across candidates |
| `GET` | `/api/resumes/{id}/similar?limit={n}` | Find similar candidates within the same role |
| `POST` | `/api/resumes/{id}/multi-role` | Score a resume against multiple roles |

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/seed` | Load demo dataset (replaces all existing data) |

---

## Deployment

### Backend — Railway

The backend ships with `Dockerfile`, `Procfile`, and `railway.toml` for Railway deployment.

1. Create a Railway project and connect it to the `backend/` directory (or root with the Railway config pointing there).
2. Add the **PostgreSQL** plugin — Railway automatically injects `DATABASE_URL`.
3. Enable the pgvector extension on the provisioned database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Set `GEMINI_API_KEY` and any other required variables in Railway's environment dashboard.
5. Deploy. Railway will use the `Dockerfile` automatically.
6. After the first deploy, seed the demo data:
   ```bash
   curl -X POST https://your-app.railway.app/api/seed
   ```

### Frontend — Vercel

1. Import the `frontend/` directory into a new Vercel project.
2. Set the environment variable `NEXT_PUBLIC_API_URL` to your deployed Railway backend URL.
3. Deploy.

### Supabase Storage (Optional)

1. Create a Supabase project.
2. Go to **Storage** → create a bucket named `resumes`.
3. Copy the **Project URL** and **anon key** into the Railway environment variables (`SUPABASE_URL`, `SUPABASE_KEY`).
