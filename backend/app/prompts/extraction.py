"""PE-03: Evidence-anchored resume extraction prompt."""

SYSTEM = """You are a structured data extraction specialist. Extract ONLY what is explicitly stated in the resume text.

Critical rules:
1. For every field: return the extracted value AND the verbatim text that supports it (max 15 words).
2. If text does not contain evidence for a field: return null for both value and evidence.
3. Do NOT infer, extrapolate, or use external knowledge. Null is the correct answer when evidence is absent.
4. Do NOT normalize values — return exactly what the resume states.
5. Return ONLY valid JSON. No prose, no markdown."""


def build_extraction_prompt(resume_text: str, extraction_fields: list[dict]) -> str:
    fields_desc = "\n".join(
        f'- "{f["field"]}": {f.get("description", f["label"])} (type: {f.get("type", "text")})'
        for f in extraction_fields
        if f.get("enabled", True)
    )

    field_names = [f["field"] for f in extraction_fields if f.get("enabled", True)]
    example_fields = "\n".join(
        f'    "{name}": {{"value": null, "evidence": null, "confidence": "absent"}}'
        for name in field_names
    )

    return f"""Extract the following fields from this resume.

FIELDS TO EXTRACT:
{fields_desc}

RESUME TEXT:
{resume_text}

Return JSON in this exact format:
{{
  "fields": {{
{example_fields}
  }}
}}

For each field, use:
- "value": the extracted value (string, number, or array as appropriate; null if absent)
- "evidence": verbatim quote from resume supporting the value (max 15 words; null if absent)
- "confidence": "high" | "medium" | "low" | "absent"

For type "list" fields (like skills), return value as an array of strings."""
