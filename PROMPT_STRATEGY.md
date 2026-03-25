# Prompt Engineering Strategy — Sprinto AI Resume Screener

## Overview of All LLM Calls

| ID | Name | Purpose | When Called |
|----|------|---------|------------|
| PE-01 | JD Decomposition | Parse JD into must/should/nice-to-have hierarchy | Once per role, cached |
| PE-02 | JD Quality Analysis | Flag contradictions, vague requirements, bias signals | Same call as PE-01 |
| PE-03 | Resume Extraction | Structured extraction with verbatim evidence anchoring | Once per upload (or re-parse) |
| PE-04 | Contradiction Detection | Flag internal resume inconsistencies | Deterministic (no LLM) |
| PE-05 | Raw Dimensional Scoring | Score 4 dimensions with evidence citations | Per candidate × role |
| PE-06 | Adversarial Critique | Self-critique of PE-05 scores, find overrating | Per candidate × role |
| PE-07 | Score Synthesis | Recruiter summary, strengths, concerns, questions | Per candidate × role |
| PE-08 | AI Authorship Signal | Detect AI-generated resume content | Per upload |

---

## PE-01 + PE-02: JD Decomposition + Quality Analysis

**Design:** Single combined call to reduce API costs. Returns both decomposed requirements and quality flags.

**Key decisions:**
- Role level extraction (`junior | mid | senior | ...`) feeds into scoring calibration
- `measurement_signals` per requirement give the scoring prompt concrete evidence targets
- Quality flags surface BEFORE resumes are uploaded — fixes root cause rather than symptoms
- Bias signal detection (prestige schools, "culture fit") aligned with EU AI Act compliance intent

**Anti-hallucination:** Every requirement must be traceable to JD text or marked `[implicit]`. JSON-only output enforced via `response_mime_type="application/json"`.

---

## PE-03: Resume Extraction

**Design:** Single-pass extraction with mandatory evidence anchoring.

**Critical constraints:**
```
For every field: return the value AND the verbatim text (max 15 words).
If evidence is absent: return null for both. Null is the correct answer.
Do NOT infer, extrapolate, or use external knowledge.
```

**Why evidence anchoring matters:**
- Makes every claim verifiable by the recruiter (click to see source)
- Prevents hallucination of qualifications not present in the resume
- The 15-word limit forces precise quotes, not paraphrases

**Pydantic validation:** All extraction outputs are validated for schema compliance. If validation fails, the specific failing field is retried with a simplified prompt.

---

## PE-05: Raw Dimensional Scoring

**Design:** Scores 4 dimensions independently to prevent halo effect contamination.

**The critical calibration rule:**
```
Score 8-10: TWO or more specific, independent evidences required
Score 6-7:  ONE strong evidence or TWO weak evidences
Score 4-5:  Ambiguous or partial evidence
Score 1-3:  Evidence absent or directly contradicts requirement
```

**Why this rule is the most important constraint:**
Without it, LLMs produce score inflation (everything 6-8, no differentiation). The "two evidences for 8+" rule forces genuine discrimination between candidates.

**Dimensions:**
- Technical Skills (weight: 1.4)
- Experience Depth (weight: 1.1)
- Domain Relevance (weight: 1.0)
- Career Trajectory (weight: 0.9)

---

## PE-06: Adversarial Critique

**Design:** A second LLM call that explicitly challenges the PE-05 scores.

**Why two stages?**
Single-pass scoring produces grade inflation. The adversarial persona creates pressure to find genuine weaknesses. Key instruction:
```
"Push back on at least half the dimensions — because there almost always is something."
```

**Score blending:**
- Final score = 60% PE-05 raw + 40% PE-06 adjusted
- This weighting preserves the positive evidence while incorporating legitimate critique
- Both stages stored in DB for full transparency (accessible via "Show AI Reasoning" toggle)

---

## PE-07: Score Synthesis

**Design:** Produces the recruiter-facing output — structured, copy-paste ready.

**Key constraints:**
```
Every sentence must contain a fact. No filler. No hedging.
3 sentences maximum for recruiter_summary.
Suggested questions must target specific identified gaps.
```

**Output fields:**
- `strengths`: 3 specific strengths with verbatim evidence
- `concerns`: 2 concerns with suggested interview questions
- `recruiter_summary`: 3 sentences, copy-paste ready
- `recommendation`: strongly_recommend | recommend | maybe | do_not_advance
- `suggested_questions`: targeted to specific gaps in the score

---

## PE-08: AI Authorship Signal

**Design:** Lightweight classifier. Does NOT affect the score — information only.

**Why this matters:**
64% of recruiters reported increased AI-generated resume volume (2024-25). The recruiter deserves to know if descriptions may not reflect conversational fluency.

**Indicators assessed:**
- Uniform sentence structure across all job descriptions
- Every bullet has a percentage or metric
- Vocabulary elevated relative to experience level
- Loss of personal voice

**Surfaced as:** Badge on candidate card ("AI-written signal: moderate"), not a score penalty.

---

## Prompt Versioning

All prompt templates are defined in `backend/app/prompts/`. To modify safely:

1. Read the constraint rationale above before changing any rule
2. Test on at least 5 diverse resumes before deploying
3. Compare score distributions before/after (mean should stay 5-7 for average candidates)
4. The adversarial critique stage is the most sensitive — changes can destabilize the blend

**Safe to modify:** Synthesis tone, summary length, question format
**Modify carefully:** Evidence anchoring constraints, scoring calibration rules
**Do not remove:** The "two evidences for 8+" rule, the null instruction, the adversarial pushback requirement
