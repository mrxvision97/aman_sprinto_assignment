# Sprinto AI Resume Screener — Frontend

The Next.js 14 frontend for the Sprinto AI Resume Screener. Provides a fully responsive UI for managing hiring roles, uploading and reviewing resumes, viewing AI-generated scores, and searching candidates semantically.

For the full project overview, architecture, and backend setup, see the [root README](../README.md).

---

## Tech Stack

| | |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Data Fetching | SWR with custom polling hook |
| Icons | Lucide React |
| Notifications | Sonner |

---

## Key Pages & Components

| Route | Description |
|---|---|
| `/` | Home — role list with resume counts, average scores; create new role with optional JD preview |
| `/roles/[id]` | Role detail — drag-and-drop upload zone, live processing status, ranked candidate list, semantic search |
| `/roles/[id]/settings` | Role settings — JD editor + quality analysis, blind mode toggle, extraction field config, batch re-parse, delete role |
| `/roles/[id]/candidates/[cid]` | Candidate detail — full score breakdown, dimensional scores, strengths/concerns, suggested interview questions, parsed resume text |

### Notable Components

- **UploadZone** — Drag-and-drop or click-to-upload. Accepts all supported resume formats (PDF, DOCX, images, etc.). Shows per-file upload status.
- **ScoreCard** — Candidate summary card with overall score bar, recommendation badge, confidence indicator, similar-candidate finder, and delete action.
- **JDQualityNotice** — Displays flagged JD quality issues (vague requirements, missing must-haves, bias signals) returned by the analyzer.
- **StatusBadge** — Color-coded badge tracking resume pipeline state (`pending`, `parsing`, `extracting`, `scoring`, `scored`, `error`, `duplicate`).
- **use-polling** — SWR-based hook that polls an endpoint on a configurable interval and stops automatically when the component unmounts.

---

## Getting Started

```bash
npm install

# Point at your backend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

App runs at `http://localhost:3000`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## Available Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## Deployment

Deploy to Vercel in one step:

1. Import this directory (`frontend/`) into a Vercel project.
2. Set `NEXT_PUBLIC_API_URL` to your deployed backend URL.
3. Deploy — Vercel auto-detects Next.js and sets the build command.
