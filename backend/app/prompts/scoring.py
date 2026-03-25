"""PE-05: Raw dimensional scoring prompt."""

SYSTEM = """You are a rigorous technical recruiter scoring a candidate against a job description.

Scoring calibration — STRICTLY follow this:
- Score 8-10: Only when you can cite TWO or more specific, independent evidences from the resume.
- Score 6-7: ONE strong evidence or TWO weak evidences.
- Score 4-5: Evidence is ambiguous, partial, or inferred.
- Score 1-3: Evidence is absent or directly contradicts the requirement.
- Score each dimension INDEPENDENTLY — do not let overall impression influence individual scores.

Return ONLY valid JSON. No prose outside the JSON."""


def build_scoring_prompt(extracted_fields: dict, jd_decomposed: dict, jd_text: str, rag_context: str = "") -> str:
    rag_section = f"\nRELEVANT RESUME SECTIONS (from semantic search):\n{rag_context}\n" if rag_context else ""

    must_haves = jd_decomposed.get("must_haves", [])
    should_haves = jd_decomposed.get("should_haves", [])

    must_text = "\n".join(f"- {r.get('requirement', r) if isinstance(r, dict) else r}" for r in must_haves[:8])
    should_text = "\n".join(f"- {r.get('requirement', r) if isinstance(r, dict) else r}" for r in should_haves[:5])

    return f"""Score this candidate against the job description on 4 dimensions.

JOB DESCRIPTION (key requirements):
MUST HAVE:
{must_text or jd_text[:800]}

SHOULD HAVE:
{should_text}

CANDIDATE DATA:
{_format_fields(extracted_fields)}
{rag_section}

Score on these 4 dimensions (0-10 scale):
1. Technical Skills — Does the candidate have the technical skills required?
2. Experience Depth — Years, seniority, and complexity of relevant experience?
3. Domain Relevance — How closely does their background match this domain/industry?
4. Career Trajectory — Is their growth trajectory aligned with this role level?

Return JSON:
{{
  "dimensions": [
    {{
      "dimension": "Technical Skills",
      "score": <0-10>,
      "evidence": ["<verbatim quote 1>", "<verbatim quote 2>"],
      "gaps": ["<what is missing for a higher score>"]
    }},
    ...
  ],
  "overall_impression": "<1 sentence>"
}}"""


def _format_fields(fields: dict) -> str:
    lines = []
    for key, val in fields.items():
        if isinstance(val, dict):
            v = val.get("value")
            e = val.get("evidence")
            if v is not None:
                lines.append(f"- {key}: {v}" + (f' (evidence: "{e}")' if e else ""))
        else:
            if val is not None:
                lines.append(f"- {key}: {val}")
    return "\n".join(lines) if lines else "No extracted fields available"
