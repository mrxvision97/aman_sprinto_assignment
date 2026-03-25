# System Architecture — Sprinto AI Resume Screener

## System Diagram

```
Browser (Vercel)
    │ HTTPS
    ▼
Next.js 14 App Router
    │ SWR polling (3s) for live status updates
    ▼
FastAPI Backend (Railway)
    ├── /api/roles          Role CRUD + JD analysis
    ├── /api/resumes        Upload + pipeline trigger
    ├── BackgroundTasks     Async pipeline per resume
    │
    ├──► PostgreSQL + pgvector (Railway)
    │    ├── roles, resumes, scores
    │    └── resume_chunks (HNSW index for RAG)
    │
    ├──► Supabase Storage
    │    └── Raw PDF/DOCX files
    │
    └──► Google Gemini API
         ├── gemini-2.0-flash (LLM)
         └── text-embedding-004 (768-dim vectors)
```

## AI Pipeline (per resume)

```
Upload
  │
  ▼
PARSE (pdfplumber / python-docx)
  → parsed_text, parse_report{confidence, sections}
  │
  ▼
EXTRACT (PE-03: Gemini)
  → extracted_fields{field: {value, evidence, confidence}}
  │
  ├──► Contradiction Detection (deterministic)
  │    → contradiction_flags[{type, description, severity}]
  │
  ├──► AI Authorship Signal (PE-08: Gemini)
  │    → ai_authorship_signal: none|weak|moderate|strong
  │
  ▼
EMBED (Gemini text-embedding-004)
  → resume_chunks with 768-dim vectors in pgvector
  │
  ▼
JD DECOMPOSE (PE-01+02: Gemini, cached per role)
  → must_haves, should_haves, quality_flags
  │
  ▼
RAG RETRIEVAL (pgvector cosine similarity)
  → top-k relevant chunks per JD requirement
  │
  ▼
SCORE RAW (PE-05: Gemini)
  → 4 dimensional scores with evidence + gaps
  │
  ▼
ADVERSARIAL CRITIQUE (PE-06: Gemini)
  → challenges each score, finds overrating
  │
  ▼
BLEND: 60% raw + 40% critique adjusted
  → final dimensional_scores, overall_score
  │
  ▼
SYNTHESIZE (PE-07: Gemini)
  → recruiter_summary, strengths, concerns, questions
  │
  ▼
status: scored → displayed in ranked list
```

## Database Schema

### `roles`
Stores role title, JD text, cached JD decomposition, extraction config, blind mode setting.

### `resumes`
Stores parsed text, extracted fields with evidence, contradiction flags, AI authorship signal, processing status. PII (name/email) stored here but stripped before scoring when blind mode is active.

### `scores`
Stores dimensional scores (raw + after critique), overall score, recruiter summary, strengths, concerns, suggested interview questions. Also stores raw PE-05 and PE-06 outputs for the "Show AI Reasoning" feature.

### `resume_chunks`
Section-level chunks of resume text with 768-dim pgvector embeddings. Indexed with HNSW for fast similarity search.

## Technology Decisions

| Component | Choice | Reason | Trade-off |
|-----------|--------|--------|-----------|
| LLM | Gemini 2.0 Flash | Fast, cheap, excellent JSON output | 15 RPM free tier limit |
| Embeddings | Gemini text-embedding-004 | Same API key, 768-dim, good quality | Slightly lower quality than OpenAI ada-002 |
| Vector DB | pgvector on PostgreSQL | Single database, no sync complexity | Slower than Pinecone at >5M vectors |
| Async | FastAPI BackgroundTasks | Simpler than Celery for prototype | No persistent task queue |
| File storage | Supabase Storage | Free tier, simple SDK, CORS support | Not as mature as S3 |
| Frontend | Next.js 14 | App Router, SWR, Vercel deploy | Heavier than Vite for SPA |

## Rate Limiting Strategy

Gemini free tier: 15 RPM. Each resume needs ~5-6 LLM calls.
- `asyncio.Semaphore(1)`: ensures one call at a time
- 4-second minimum interval between calls
- Exponential backoff on 429 errors (3 retries)
- Result: ~20-25 seconds per resume, 30 resumes in ~12 minutes

## Bias & Fairness Architecture

1. **Blind Mode (default on)**: PII fields (name, email, phone) are stripped from `extracted_fields` before the scoring LLM call. The scoring model evaluates skills and experience only.

2. **Language Neutrality**: PE-05 scoring prompt explicitly instructs: evaluate only evidence of skills, experience, and role progression — not vocabulary, tone, or writing style.

3. **Gap Contextualisation**: Contradiction detection flags gaps but doesn't penalise them. Scoring prompts do not instruct penalisation of employment gaps.

4. **Human Override Required**: No candidate is ever auto-rejected by the system. All outputs are recommendations. Status changes require human action.

## Scaling Considerations

Current prototype scales to:
- ~1,000 resumes/day (Gemini rate limit bound)
- ~100,000 vector chunks (pgvector HNSW handles efficiently)
- ~50 concurrent users (Railway free tier)

Production upgrades:
- Celery + Redis for reliable background job queue
- pgvector → Pinecone at >5M vectors
- Gemini API → paid tier or multiple API keys for higher RPM
- Railway → AWS ECS for auto-scaling
