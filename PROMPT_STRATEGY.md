# Prompt Engineering Strategy — Sprinto AI Resume Screener

## Overview of All LLM Calls

| ID | Name | Purpose | When Called | Gemini Calls |
|---|---|---|---|---|
| PE-01 | JD Decomposition | Parse JD into must/should/nice-to-have hierarchy | Once per role, result cached in DB | 1 (combined with PE-02) |
| PE-02 | JD Quality Analysis | Flag contradictions, vague requirements, bias signals | Same call as PE-01 | — |
| PE-03 | Resume Extraction | Structured extraction with verbatim evidence anchoring | Once per upload (or batch re-parse) | 1 |
| PE-04 | Contradiction Detection | Flag internal resume inconsistencies | Per upload (deterministic — no LLM) | 0 |
| PE-05 | Raw Dimensional Scoring | Score 4 dimensions with evidence citations | Per candidate × role | 1 |
| PE-06 | Adversarial Critique | Self-critique of PE-05 scores, find overrating | Per candidate × role | 1 |
| PE-07 | Score Synthesis | Recruiter summary, strengths, concerns, questions | Per candidate × role | 1 |
| PE-08 | AI Authorship Signal | Detect AI-generated resume prose | Per upload | 1 |

**Total Gemini calls per resume: ~5** (PE-03 + PE-05 + PE-06 + PE-07 + PE-08; PE-01/02 amortized across all uploads for that role).

---

## PE-01 + PE-02: JD Decomposition + Quality Analysis

**File:** `backend/app/prompts/jd_decomposition.py`

**Design:** A single combined call to reduce API costs. Returns both structured requirements and quality flags in one JSON response.

**System persona:**
> "You are a senior talent acquisition specialist who has read thousands of job descriptions."

**Output structure:**
```json
{
  "decomposed": {
    "role_level": "junior | mid | senior | staff | principal | executive",
    "must_haves": [{ "requirement": "...", "measurement_signals": ["...", "..."] }],
    "should_haves": [{ "requirement": "...", "measurement_signals": ["..."] }],
    "nice_to_haves": ["..."],
    "implicit_requirements": [{ "requirement": "...", "reasoning": "..." }]
  },
  "quality_report": {
    "flags": [{ "flag": "...", "severity": "error|warning|info", "suggestion": "..." }],
    "overall_quality": "good | fair | poor",
    "summary": "..."
  }
}
```

**Key design decisions:**
- `measurement_signals` per requirement give PE-05 concrete, objective evidence targets to look for — preventing subjective judgment.
- `implicit_requirements` surface unstated expectations (e.g., "this senior role implies leadership experience") so scoring doesn't miss them.
- Quality flags are surfaced to the recruiter **before** any resume is uploaded — fixing root cause rather than patching symptoms downstream.
- Bias signal detection (`"top university"`, `"culture fit"` without definition) is flagged at PE-02 to prompt JD improvement, aligned with fair hiring practice.
- Result is cached in `roles.jd_decomposed` and `roles.jd_quality_report`. Re-running the analysis (after editing the JD) invalidates and overwrites the cache.

**Anti-hallucination:** `response_mime_type="application/json"` enforced at the Gemini SDK level. Every requirement must be traceable to JD text or explicitly marked as implicit.

---

## PE-03: Resume Extraction

**File:** `backend/app/prompts/extraction.py`

**Design:** Single-pass extraction across all configured fields. Every field must return a verbatim evidence quote alongside its value.

**System persona:**
> "You are a structured data extraction specialist. Extract ONLY what is explicitly stated in the resume text."

**Critical constraints in the prompt:**
```
1. For every field: return the extracted value AND the verbatim text that supports it (max 15 words).
2. If text does not contain evidence for a field: return null for both value and evidence.
3. Do NOT infer, extrapolate, or use external knowledge. Null is the correct answer when evidence is absent.
4. Do NOT normalize values — return exactly what the resume states.
```

**Output per field:**
```json
{
  "full_name": { "value": "Jane Smith", "evidence": "Jane Smith | jane@email.com", "confidence": "high" },
  "total_experience_years": { "value": null, "evidence": null, "confidence": "absent" }
}
```

**Why evidence anchoring matters:**
- Every extracted claim is verifiable — recruiters can see the exact source text.
- Prevents hallucination of qualifications not present in the resume.
- The 15-word limit forces precise verbatim quotes, not LLM paraphrases.
- `confidence` field (`high / medium / low / absent`) lets the UI signal uncertainty.

**Configurable fields:** The prompt is dynamically built from `role.extraction_config`. Adding a custom field in the UI changes the extraction prompt for all subsequent uploads and re-parses.

**Service-level validation:** `extractor.py` validates that every enabled field in the config is present in the response. Missing fields are back-filled with `{ value: null, evidence: null, confidence: "absent" }` rather than surfacing an error.

---

## PE-04: Contradiction Detection

**File:** `backend/app/services/contradiction.py`

**Design:** Fully deterministic — no LLM call. Contradiction flags are computed from `extracted_fields` using rule-based logic.

**Checks performed:**
- Employment date overlaps (same candidate listed at two employers in the same month)
- Years-of-experience vs. graduation-date math (e.g., "10 years experience" but graduated 3 years ago)
- Title vs. seniority level mismatches

**Why deterministic rather than LLM?**
- Zero additional API cost or latency.
- Deterministic output is auditable — the exact rule that fired is recorded.
- LLMs hallucinate contradiction flags; date math is better served by code.

**Output:** `contradiction_flags` stored on the resume; surfaced as warning badges on the candidate detail page.

---

## PE-05: Raw Dimensional Scoring

**File:** `backend/app/prompts/scoring.py`

**Design:** Scores 4 dimensions **independently** to prevent halo-effect contamination from an overall impression.

**System persona:**
> "You are a rigorous technical recruiter scoring a candidate against a job description."

**The calibration rule — the most important constraint in the entire system:**
```
Score 8-10: Only when you can cite TWO or more specific, independent evidences.
Score 6-7:  ONE strong evidence or TWO weak evidences.
Score 4-5:  Evidence is ambiguous, partial, or inferred.
Score 1-3:  Evidence is absent or directly contradicts the requirement.
Score each dimension INDEPENDENTLY — do not let overall impression influence individual scores.
```

**Why this rule is critical:** Without an explicit calibration rule, LLMs produce score inflation — everything clusters between 6 and 8, making ranking meaningless. The "two evidences for 8+" rule forces genuine discrimination between strong and average candidates.

**Dimensions and weights:**
| Dimension | Weight | Rationale |
|---|---|---|
| Technical Skills | 1.4 | Most directly job-relevant |
| Experience Depth | 1.1 | Seniority and complexity matter |
| Domain Relevance | 1.0 | Industry/domain alignment |
| Career Trajectory | 0.9 | Growth signal, secondary |

**RAG integration:** The scoring prompt includes a `RELEVANT RESUME SECTIONS` block when RAG context is available (≥5 chunks in the role corpus, similarity threshold >0.5). This grounds the model in actual resume passages rather than relying solely on extracted field summaries.

**Output:**
```json
{
  "dimensions": [
    { "dimension": "Technical Skills", "score": 7, "evidence": ["..."], "gaps": ["..."] }
  ],
  "overall_impression": "..."
}
```

---

## PE-06: Adversarial Critique

**File:** `backend/app/prompts/critique.py`

**Design:** A second independent LLM call that explicitly challenges the PE-05 scores. Uses a deliberately skeptical persona.

**System persona:**
> "You are a skeptical senior hiring manager reviewing AI-generated screening scores. You have seen these systems over-score candidates before. Find what was overrated."

**Key instruction:**
```
Push back on at least half the dimensions — because there almost always is something.
```

**Why two stages rather than one?**
Single-pass scoring produces grade inflation even with the calibration rule, because the same model that assigned a score cannot effectively challenge its own reasoning in the same context. Splitting into two separate calls with adversarial framing consistently produces more calibrated scores.

**Score blending formula:**
```
final_score = (pe05_raw × 0.6) + (pe06_adjusted × 0.4)
```

The 60/40 weighting preserves the positive evidence found in Stage 1 while incorporating legitimate critique from Stage 2. Both the raw PE-05 output and the PE-06 critique are stored in `scores.raw_scores` and `scores.critique` for full transparency.

**Output:**
```json
{
  "critiques": [
    {
      "dimension": "Technical Skills",
      "original_score": 8,
      "critique": "Python mentioned once without depth. No project evidence cited.",
      "adjusted_score": 6,
      "adjustment_reason": "Single weak mention doesn't justify 8"
    }
  ]
}
```

---

## PE-07: Score Synthesis

**File:** `backend/app/prompts/synthesis.py`

**Design:** Produces the recruiter-facing output — structured, fact-dense, copy-paste ready. Runs after blending is complete so it operates on final scores.

**System persona:**
> "You are writing a 30-second briefing for a recruiter presenting to a hiring manager. Every sentence must contain a fact. No filler. No hedging."

**Key output constraints:**
```
- recruiter_summary: 3 sentences maximum. Copy-paste ready. Cite specific evidence. State honestly what is missing.
- strengths: 3 items with verbatim evidence from their history
- concerns: 2 items with a suggested interview question per concern
- suggested_questions: targeted to specific identified gaps
```

**Output:**
```json
{
  "strengths": [{ "point": "...", "evidence": "..." }],
  "concerns": [{ "point": "...", "evidence": "...", "suggested_question": "..." }],
  "recruiter_summary": "...",
  "recommendation": "strongly_recommend | recommend | maybe | do_not_advance",
  "recommendation_reason": "...",
  "suggested_questions": [{ "question": "...", "addresses": "..." }],
  "confidence": "high | medium | low"
}
```

**Recommendation mapping:**

| Tier | Typical Score Range | Meaning |
|---|---|---|
| `strongly_recommend` | 8.0 – 10.0 | Advance immediately |
| `recommend` | 6.5 – 7.9 | Advance with normal process |
| `maybe` | 4.5 – 6.4 | Proceed with caveats or screen call first |
| `do_not_advance` | 0 – 4.4 | Significant gaps relative to JD |

Thresholds are guidance — PE-07 assigns recommendation based on holistic assessment, not strict score cutoffs.

---

## PE-08: AI Authorship Signal

**File:** `backend/app/prompts/ai_authorship.py`

**Design:** A lightweight classifier run after extraction. Does **not** affect the score — it is information for the recruiter only.

**System persona:**
> "Assess whether resume text shows indicators of AI generation. This is calibration information for the recruiter — not a judgment."

**Indicators assessed:**
- Uniform sentence structure across all job descriptions
- Every bullet contains a percentage or quantified metric
- Near-identical grammatical structure in every experience item
- Vocabulary unusually elevated relative to claimed experience level
- Loss of personal voice throughout

**Output:**
```json
{
  "signal": "none | weak | moderate | strong",
  "rationale": "...",
  "indicators_found": ["..."]
}
```

**Why this matters:** Recruiters increasingly report AI-inflated resumes that do not reflect the candidate's actual communication fluency. The signal is surfaced as a badge on the candidate card — it prompts human judgment, not automated rejection.

**Scope limitation:** Only the first 1500 characters of the resume are analyzed to keep token usage low. This is sufficient for detecting broad stylistic patterns.

---

## Multi-Role Comparison

**Service:** `backend/app/services/multi_role.py`

**Design:** Re-runs PE-05 → PE-06 → PE-07 against each target role's JD decomposition using the already-extracted fields from the resume. No re-parsing or re-extraction.

**Pre-condition:** Resume must be in `scored` status (`extracted_fields` and `parsed_text` must be present).

**Use case:** A candidate suitable for multiple open roles — compare scores across roles without re-uploading.

---

## Prompt Versioning & Safety Guidelines

All prompt templates live in `backend/app/prompts/`. Before modifying any prompt:

1. Read the constraint rationale in this document for the prompt you are changing.
2. Test on at least 5 diverse resumes before deploying to production.
3. Compare score distributions before and after (mean should stay 5.0–7.0 for average candidates; std dev should stay ≥1.5 for meaningful ranking).
4. The adversarial critique stage (PE-06) is the most sensitive — small wording changes to the skeptical persona can destabilize the blend significantly.

| Change | Safety Level |
|---|---|
| Synthesis tone, summary length, question format (PE-07) | Safe to modify |
| Scoring dimensions or weights (PE-05) | Modify carefully — affects ranking |
| Evidence anchoring constraints (PE-03) | Modify carefully — affects hallucination rate |
| Scoring calibration rule (PE-05) | Do not remove the "two evidences for 8+" rule |
| Adversarial pushback instruction (PE-06) | Do not remove the "push back on half" instruction |
| Null extraction instruction (PE-03) | Do not remove — prevents fabrication |
