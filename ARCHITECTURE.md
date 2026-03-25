# System Architecture — Sprinto AI Resume Screener

## System Diagram

```
Browser (Vercel)
    │ HTTPS
    ▼
Next.js 14 App Router
    │ SWR polling (3–5s) for live status updates
    ▼
FastAPI Backend (Railway)
    ├── /api/roles          Role CRUD, JD analysis, config, batch-reparse
    ├── /api/resumes        Upload, list, search, similar, multi-role
    ├── BackgroundTasks     Async pipeline per resume
    │
    ├──► PostgreSQL + pgvector (Railway)
    │    ├── roles, resumes, scores
    │    └── resume_chunks (3072-dim HNSW index for RAG + search)
    │
    ├──► Supabase Storage
    │    └── Raw resume files (PDF, DOCX, images, etc.)
    │
    └──► Google Gemini API
         ├── gemini-2.0-flash      (LLM — all structured calls)
         └── gemini-embedding-001  (3072-dim vectors)
```

---

## AI Pipeline (per resume upload)

```
Upload
  │
  ├── Layer 1 duplicate check: SHA-256 file hash (immediate return if match)
  │
  ▼
STEP 1 — PARSE
  Primary:  Unstructured.io API (hi_res for PDFs/images, parallel page split)
  Fallback: pdfplumber (PDF) | python-docx (DOCX)
  → parsed_text, parse_report { confidence, method, sections_found, char_count }
  │
  ▼
STEP 2 — EXTRACT (PE-03: Gemini 2.0 Flash)
  → extracted_fields { field: { value, evidence, confidence } }
  │
  ├── Layer 2 duplicate check: identity fingerprint (name + email hash)
  │   → status = "duplicate", duplicate_of_id set (if match found)
  │
  ▼
STEP 3 — CONTRADICTION DETECTION (deterministic)
  → contradiction_flags [{ type, description, severity }]
  │
  ▼
STEP 4 — AI AUTHORSHIP SIGNAL (PE-08: Gemini 2.0 Flash)
  → ai_authorship_signal: none | weak | moderate | strong
  │
  ▼
STEP 5 — CHUNK + EMBED (Gemini Embedding-001)
  → resume split into sections (contact, experience, education, skills, …)
  → each chunk embedded → 3072-dim vector → resume_chunks table (pgvector)
  │
  ▼
STEP 6 — JD DECOMPOSE (PE-01 + PE-02: Gemini 2.0 Flash, cached per role)
  → must_haves [{ requirement, measurement_signals }]
  → should_haves, nice_to_haves, implicit_requirements
  → quality_report { flags, overall_quality }
  │
  ▼
STEP 7 — RAG RETRIEVAL (pgvector cosine similarity)
  Threshold: only when ≥ 5 chunks exist in the role corpus
  → for each of top 3 must_have requirements:
      embed query "Evidence of: <requirement>"
      → retrieve best matching chunk (similarity > 0.5)
  → rag_context string injected into scoring prompt
  │
  ▼
STEP 8 — BLIND MODE PII STRIP (if enabled)
  → name, email, phone removed from extracted_fields before LLM sees them
  │
  ▼
STEP 9 — SCORE (PE-05 + PE-06 + PE-07: three Gemini calls)
  │
  ├── PE-05 Raw Scoring
  │   → 4 dimensions × { score, evidence[], gaps[] }
  │
  ├── PE-06 Adversarial Critique
  │   → challenges each dimension score, produces adjusted_score per dim
  │
  ├── BLEND: final_score = raw × 0.6 + adjusted × 0.4
  │   Weighted overall: Technical Skills ×1.4, Experience Depth ×1.1,
  │                     Domain Relevance ×1.0, Career Trajectory ×0.9
  │
  └── PE-07 Synthesis
      → recruiter_summary, strengths[], concerns[], suggested_questions[]
      → recommendation: strongly_recommend | recommend | maybe | do_not_advance
      → confidence: high | medium | low
  │
  ▼
STEP 10 — PERSIST
  → Score row saved; resume.status = "scored"
  → Displayed in ranked candidate list
```

---

## Database Schema

### `roles`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `title` | VARCHAR(255) | Role title |
| `jd_text` | TEXT | Full job description |
| `jd_decomposed` | JSONB | Cached PE-01 output (must/should/nice-to-have) |
| `jd_quality_report` | JSONB | Cached PE-02 output (flags, overall quality) |
| `extraction_config` | JSONB | List of extraction field definitions |
| `extraction_config_version` | INTEGER | Incremented on each config change |
| `blind_mode` | BOOLEAN | Default `true` — strips PII before scoring |
| `status` | VARCHAR(20) | `active` / `archived` |
| `created_at` | TIMESTAMPTZ | |

### `resumes`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `role_id` | UUID FK → roles | Cascade delete |
| `original_filename` | VARCHAR(255) | |
| `file_hash` | VARCHAR(64) | SHA-256 — Layer 1 duplicate check |
| `storage_path` | VARCHAR(512) | Supabase Storage path |
| `parsed_text` | TEXT | Full extracted resume text |
| `parse_report` | JSONB | Confidence, method, sections, warnings |
| `extracted_fields` | JSONB | PE-03 output: `{ field: { value, evidence, confidence } }` |
| `extraction_config_version` | INTEGER | Version at time of extraction |
| `contradiction_flags` | JSONB | Detected resume inconsistencies |
| `ai_authorship_signal` | VARCHAR(20) | `none / weak / moderate / strong` |
| `duplicate_of_id` | UUID FK → resumes | Set on Layer 2 duplicate match |
| `status` | VARCHAR(30) | `pending / parsing / extracting / scoring / scored / duplicate / error` |
| `error_message` | TEXT | Last pipeline error (truncated to 500 chars) |
| `uploaded_at` | TIMESTAMPTZ | |

### `scores`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `resume_id` | UUID FK → resumes | Cascade delete; unique per (resume, role) |
| `role_id` | UUID FK → roles | |
| `dimensional_scores` | JSONB | Final blended scores per dimension with evidence |
| `overall_score` | NUMERIC(3,1) | Weighted average across dimensions |
| `raw_scores` | JSONB | PE-05 output stored for transparency |
| `critique` | JSONB | PE-06 output stored for transparency |
| `strengths` | JSONB | PE-07 strengths with evidence |
| `concerns` | JSONB | PE-07 concerns with suggested questions |
| `recruiter_summary` | TEXT | PE-07 recruiter-facing paragraph |
| `recommendation` | VARCHAR(30) | `strongly_recommend / recommend / maybe / do_not_advance` |
| `suggested_questions` | JSONB | Interview questions per identified gap |
| `confidence` | VARCHAR(10) | `high / medium / low` |
| `created_at` | TIMESTAMPTZ | |

### `resume_chunks`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `resume_id` | UUID FK → resumes | Cascade delete |
| `role_id` | UUID FK → roles | Denormalized for fast per-role queries |
| `section_type` | VARCHAR(50) | `contact / experience / education / skills / projects / summary / …` |
| `chunk_text` | TEXT | Up to 1500 chars per chunk |
| `chunk_index` | SMALLINT | Position within the resume |
| `embedding` | Vector(3072) | Gemini Embedding-001 vector (pgvector) |
| `created_at` | TIMESTAMPTZ | |

---

## Semantic Search & Similarity

Two distinct pgvector query patterns are used:

**Semantic Search** (`GET /api/roles/{id}/search?q=`):
```sql
SELECT resume_id, MIN(embedding <=> :query_vec::vector) AS best_distance
FROM resume_chunks
WHERE role_id = :role_id AND embedding IS NOT NULL
GROUP BY resume_id
ORDER BY best_distance
LIMIT :limit
```
The query text is embedded at request time. Results are ranked by cosine distance.

**Similar Candidates** (`GET /api/resumes/{id}/similar`):
The target resume's chunks are averaged into a single centroid vector, then the same query runs excluding the source resume. Returns candidates with the most similar overall profile.

**RAG retrieval** uses the same query pattern but per JD requirement, filtered to `similarity > 0.5`.

---

## Technology Decisions

| Component | Choice | Reason | Trade-off |
|---|---|---|---|
| LLM | Gemini 2.0 Flash | Fast, cheap, reliable JSON output mode | 15 RPM free tier limit |
| Embeddings | Gemini Embedding-001 | Same API key, 3072-dim, high quality | Higher latency than lighter models |
| Vector DB | pgvector on PostgreSQL | Single database, no sync complexity | Slower than dedicated vector DBs at >5M vectors |
| Async tasks | FastAPI BackgroundTasks | Simple, no infrastructure overhead | No persistent queue — tasks lost on crash |
| File storage | Supabase Storage | Free tier, simple SDK, CORS-friendly | Less mature than S3 |
| Frontend | Next.js 14 App Router | SWR, Vercel deploy, TypeScript | Heavier than Vite for pure SPA |
| Document parsing | Unstructured.io API + local fallback | Handles complex PDFs, multi-column, images | API call latency; fallback required for offline use |

---

## Rate Limiting Strategy

Gemini free tier: 15 RPM. Each resume requires approximately 5–6 LLM calls (extract, authorship, score, critique, synthesis; JD decomposition is cached per role).

- `asyncio.Semaphore(1)` — serializes all Gemini calls across the entire process
- 4-second minimum interval enforced between calls
- Exponential backoff on `429` / `resource_exhausted` errors (3 retries, 10s → 20s → 30s wait)
- Estimated throughput: ~25–30 seconds per resume end-to-end; ~30 resumes in ~15 minutes

---

## Bias & Fairness Architecture

1. **Blind Mode (default on)** — PII fields (`full_name`, `email`, `phone`) are stripped from `extracted_fields` in `_strip_pii()` before the scoring LLM call. The model evaluates skills, experience, and trajectory only.

2. **Language Neutrality** — PE-05 scoring prompt instructs: evaluate only evidence of skills, experience, and role progression — not vocabulary, tone, or writing style.

3. **JD Quality Pre-screening** — PE-02 flags bias signals in the job description itself (prestige-school preferences, undefined "culture fit") before any resume is evaluated.

4. **Gap Contextualisation** — Contradiction detection flags employment gaps but does not penalise them. Scoring prompts contain no instruction to penalise gaps.

5. **Human Override Required** — No candidate is ever auto-rejected. All outputs are recommendations. No status change requires anything other than human action.

---

## Scaling Considerations

Current prototype capacity:
- ~1,000 resumes/day (Gemini free tier rate-limit bound)
- ~100,000 vector chunks (pgvector HNSW handles efficiently)
- ~50 concurrent users (Railway starter tier)

Production upgrade path:
- **Celery + Redis** — persistent background job queue with retries and dead-letter handling
- **pgvector → Pinecone** — at >5M vectors for lower query latency
- **Gemini paid tier** — higher RPM; or multiple API keys round-robin
- **Railway → AWS ECS** — auto-scaling, multi-region
- **Supabase Storage → S3** — more mature lifecycle policies, presigned URLs
