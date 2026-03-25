"""JD decomposition and quality analysis (PE-01 + PE-02 combined)."""
from app.services.gemini import call_llm
from app.prompts.jd_decomposition import SYSTEM, build_jd_analysis_prompt


async def analyze_jd_quality(jd_text: str) -> dict:
    """Analyze JD and return decomposed requirements + quality flags."""
    prompt = build_jd_analysis_prompt(jd_text)
    try:
        result = await call_llm(prompt, SYSTEM)
        return {
            "decomposed": result.get("decomposed", {}),
            "quality_report": result.get("quality_report", {"flags": [], "overall_quality": "fair"}),
        }
    except Exception as e:
        return {
            "decomposed": {},
            "quality_report": {
                "flags": [{"flag": f"Analysis failed: {str(e)}", "severity": "error", "suggestion": "Try again"}],
                "overall_quality": "unknown",
            },
        }


async def get_or_create_jd_decomposition(role, db) -> dict:
    """Return cached JD decomposition or run analysis if not cached."""
    if role.jd_decomposed:
        return role.jd_decomposed

    result = await analyze_jd_quality(role.jd_text)
    role.jd_decomposed = result.get("decomposed", {})
    role.jd_quality_report = result.get("quality_report", {})
    await db.commit()
    return role.jd_decomposed
