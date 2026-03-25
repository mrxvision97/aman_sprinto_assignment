"""PE-01: JD decomposition + PE-02: JD quality analysis."""

SYSTEM = """You are a senior talent acquisition specialist who has read thousands of job descriptions.
Decompose the JD into structured requirements and identify quality issues.
Return ONLY valid JSON."""


def build_jd_analysis_prompt(jd_text: str) -> str:
    return f"""Analyze this job description.

JD TEXT:
{jd_text}

Return JSON with two sections:

1. DECOMPOSITION — structured requirements:
{{
  "role_level": "junior | mid | senior | staff | principal | executive",
  "must_haves": [
    {{"requirement": "<text>", "measurement_signals": ["<signal1>", "<signal2>"]}}
  ],
  "should_haves": [
    {{"requirement": "<text>", "measurement_signals": ["<signal1>"]}}
  ],
  "nice_to_haves": ["<text>"],
  "implicit_requirements": [
    {{"requirement": "<text>", "reasoning": "<why this is implied>"}}
  ]
}}

2. QUALITY FLAGS — identify issues:
{{
  "flags": [
    {{
      "flag": "<issue title>",
      "severity": "error | warning | info",
      "suggestion": "<how to fix>"
    }}
  ]
}}

Flag these issues:
- Contradictions (e.g., "entry level" + "5+ years required")
- Vague requirements (e.g., "strong communication skills" — not measurable from resume)
- Potential bias signals (e.g., "top university", "culture fit" without definition)
- Requirements likely to produce extremely narrow candidate pools without justification

Return as one combined JSON:
{{
  "decomposed": {{...decomposition...}},
  "quality_report": {{
    "flags": [...],
    "overall_quality": "good | fair | poor",
    "summary": "<one sentence assessment>"
  }}
}}"""
