# Sprinto AI Resume Screener

An AI-powered resume screening tool that parses resumes, extracts configurable parameters, and scores candidates against job descriptions using Google Gemini with a two-stage adversarial scoring pipeline.

**Live Demo:** [Add your Vercel URL here]
**Backend API Docs:** [Add your Railway URL]/docs

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + Tailwind CSS + shadcn/ui → Vercel |
| Backend | FastAPI + Python 3.11 → Railway |
| Database | PostgreSQL + pgvector → Railway |
| File Storage | Supabase Storage |
| LLM + Embeddings | Google Gemini 2.0 Flash + text-embedding-004 |
| Async Processing | FastAPI BackgroundTasks |

---

## Features

**Must-Haves (all complete):**
- PDF and DOCX parsing (pdfplumber + python-docx)
- Dynamic extraction with configurable parameters and evidence anchoring
- UI for adding/modifying/toggling extraction fields
- AI scoring 1-10 with dimensional breakdown and recruiter summary
- Duplicate detection (SHA-256 hash + identity fingerprint)
- Live deployment on Vercel + Railway

**Enhanced Features (all complete):**
- Batch re-parsing when config changes
- Multi-role comparison matrix
- RAG with pgvector semantic search

**Differentiators (beyond the brief):**
- JD quality analysis (flags contradictions, vague requirements, bias signals)
- Two-stage adversarial scoring (raw + self-critique for better calibration)
- Blind mode (strips PII before AI scoring to reduce bias)
- Contradiction detection (date math, employment overlaps)
- AI authorship signal detection
- Suggested interview questions per candidate
- "Show AI Reasoning" toggle reveals raw + critique stages

---

## Quick Start (Local Dev)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension

### 1. Clone and set up backend

```bash
cd backend
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Set up frontend

```bash
cd frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

### 3. Seed demo data

```bash
curl -X POST http://localhost:8000/api/seed
```

Then visit `http://localhost:3000` — you'll see a pre-loaded role with 5 ranked candidates.

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/sprinto
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## Deployment

### Railway (Backend + PostgreSQL)

1. Create a Railway project
2. Add a PostgreSQL plugin — Railway sets `DATABASE_URL` automatically
3. Enable pgvector: in Railway PostgreSQL console, run `CREATE EXTENSION vector;`
4. Set environment variables (GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, CORS_ORIGINS)
5. Deploy via GitHub: connect repo, set root directory to `/backend`
6. After deploy, seed: `curl -X POST https://your-backend.railway.app/api/seed`

### Vercel (Frontend)

1. Import GitHub repo to Vercel
2. Set root directory to `/frontend`
3. Set environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
4. Deploy

### Supabase (File Storage)

1. Create a Supabase project
2. Go to Storage → Create bucket named `resumes`
3. Set bucket to Public
4. Copy project URL and anon key to Railway env vars

---

## API Documentation

Full OpenAPI docs available at: `https://your-backend.railway.app/docs`

Key endpoints:
- `POST /api/roles` — Create role with JD
- `POST /api/roles/{id}/resumes` — Upload resume (triggers full AI pipeline)
- `GET /api/roles/{id}/resumes` — Get ranked candidates with scores
- `POST /api/roles/{id}/analyze-jd` — Run JD quality analysis
- `POST /api/resumes/{id}/multi-role` — Compare against multiple roles
- `POST /api/seed` — Load demo data

---

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design.
See [PROMPT_STRATEGY.md](./PROMPT_STRATEGY.md) for the prompt engineering strategy.
