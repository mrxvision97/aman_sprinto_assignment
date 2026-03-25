"""PE-07: Score synthesis — recruiter summary, strengths, concerns, questions."""

SYSTEM = """You are writing a 30-second briefing for a recruiter presenting to a hiring manager.
Every sentence must contain a fact. No filler. No hedging.
Return ONLY valid JSON."""


def build_synthesis_prompt(
    final_scores: list[dict], overall_score: float, jd_text: str, extracted_fields: dict
) -> str:
    dims_summary = "\n".join(
        f"- {d['dimension']}: {d['score']}/10"
        for d in final_scores
    )

    return f"""Write a recruiter briefing for this candidate.

OVERALL SCORE: {overall_score:.1f}/10

DIMENSION SCORES:
{dims_summary}

JOB DESCRIPTION (first 600 chars):
{jd_text[:600]}

CANDIDATE DATA:
{_format_fields(extracted_fields)}

Return JSON:
{{
  "strengths": [
    {{"point": "<strength title>", "evidence": "<specific evidence from their history>"}},
    {{"point": "<strength title>", "evidence": "<specific evidence>"}},
    {{"point": "<strength title>", "evidence": "<specific evidence>"}}
  ],
  "concerns": [
    {{"point": "<concern title>", "evidence": "<specific gap or risk>", "suggested_question": "<interview question that resolves this concern>"}},
    {{"point": "<concern title>", "evidence": "<specific gap or risk>", "suggested_question": "<interview question>"}}
  ],
  "recruiter_summary": "<3 sentences max. Copy-paste ready. No hedging. Cite specific evidence. State honestly what is missing.>",
  "recommendation": "strongly_recommend | recommend | maybe | do_not_advance",
  "recommendation_reason": "<one sentence justification>",
  "suggested_questions": [
    {{"question": "<specific interview question>", "addresses": "<which concern this resolves>"}},
    {{"question": "<specific interview question>", "addresses": "<which concern this resolves>"}}
  ],
  "confidence": "high | medium | low"
}}"""


def _format_fields(fields: dict) -> str:
    lines = []
    for key, val in fields.items():
        if isinstance(val, dict):
            v = val.get("value")
            if v is not None:
                lines.append(f"- {key}: {v}")
    return "\n".join(lines[:12]) if lines else "No data"
