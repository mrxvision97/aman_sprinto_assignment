"""PE-06: Adversarial self-critique prompt."""

SYSTEM = """You are a skeptical senior hiring manager reviewing AI-generated screening scores.
You have seen these systems over-score candidates before. Find what was overrated.

For at least half the dimensions, find something to push back on — because there almost always is something.
Return ONLY valid JSON."""


def build_critique_prompt(raw_scores: dict, extracted_fields: dict) -> str:
    dims = raw_scores.get("dimensions", [])
    dims_text = "\n".join(
        f"- {d['dimension']}: {d['score']}/10\n  Evidence used: {d.get('evidence', [])}"
        for d in dims
    )

    return f"""Review these AI-generated candidate scores. Find what was overrated.

STAGE 1 SCORES:
{dims_text}

CANDIDATE DATA:
{_format_brief(extracted_fields)}

For each dimension:
1. What evidence CONTRADICTS or WEAKENS the score?
2. What evidence is suspiciously ABSENT for this score level?
3. Should the score be adjusted? By how much?

Return JSON:
{{
  "critiques": [
    {{
      "dimension": "<dimension name>",
      "original_score": <number>,
      "critique": "<what is weak or missing>",
      "adjusted_score": <number>,
      "adjustment_reason": "<brief reason>"
    }}
  ]
}}"""


def _format_brief(fields: dict) -> str:
    lines = []
    for key, val in fields.items():
        if isinstance(val, dict):
            v = val.get("value")
            if v is not None:
                lines.append(f"- {key}: {v}")
    return "\n".join(lines[:10]) if lines else "No data"
