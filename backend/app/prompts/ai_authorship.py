"""PE-08: AI authorship signal detection."""

SYSTEM = """Assess whether resume text shows indicators of AI generation.
This is calibration information for the recruiter — not a judgment.
Return ONLY valid JSON."""


def build_authorship_prompt(resume_text: str) -> str:
    return f"""Assess AI-generation indicators in this resume text.

INDICATORS OF AI-GENERATION:
- Uniform sentence structure across all job descriptions
- Every bullet point contains a percentage or quantified metric
- Near-identical grammatical structure in every experience item
- Vocabulary unusually elevated relative to claimed experience level
- Overly formal, corporate language throughout without personal voice

RESUME TEXT (first 1500 chars):
{resume_text[:1500]}

Return JSON:
{{
  "signal": "none | weak | moderate | strong",
  "rationale": "<one sentence explanation>",
  "indicators_found": ["<specific indicator if any>"]
}}"""
