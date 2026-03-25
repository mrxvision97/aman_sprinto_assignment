"""PE-03: Evidence-anchored field extraction from resume text."""
from app.services.gemini import call_llm
from app.prompts.extraction import SYSTEM, build_extraction_prompt


async def extract_fields(resume_text: str, extraction_config: list[dict]) -> dict:
    """Extract structured fields from resume text with evidence anchoring."""
    enabled_fields = [f for f in extraction_config if f.get("enabled", True)]
    if not enabled_fields:
        return {}

    prompt = build_extraction_prompt(resume_text, enabled_fields)
    try:
        result = await call_llm(prompt, SYSTEM)
        fields = result.get("fields", {})
        # Validate structure — every field must have value + evidence + confidence
        validated = {}
        for field_config in enabled_fields:
            fname = field_config["field"]
            if fname in fields:
                val = fields[fname]
                if isinstance(val, dict):
                    validated[fname] = {
                        "value": val.get("value"),
                        "evidence": val.get("evidence"),
                        "confidence": val.get("confidence", "low"),
                    }
                else:
                    validated[fname] = {"value": val, "evidence": None, "confidence": "low"}
            else:
                validated[fname] = {"value": None, "evidence": None, "confidence": "absent"}
        return validated
    except Exception as e:
        return {"_extraction_error": str(e)}
