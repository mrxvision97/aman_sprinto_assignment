"""
AI scoring pipeline: PE-05 (raw scoring) + PE-06 (adversarial critique) + PE-07 (synthesis).
Two-stage design: raw scores → critique → weighted blend → recruiter summary.
"""
from app.services.gemini import call_llm
from app.prompts.scoring import SYSTEM as SCORE_SYSTEM, build_scoring_prompt
from app.prompts.critique import SYSTEM as CRITIQUE_SYSTEM, build_critique_prompt
from app.prompts.synthesis import SYSTEM as SYNTH_SYSTEM, build_synthesis_prompt


async def score_resume(
    extracted_fields: dict,
    jd_decomposed: dict,
    jd_text: str,
    rag_context: str = "",
) -> dict:
    """
    Full two-stage scoring pipeline.
    Returns dict with raw_scores, critique, final dimensional_scores, overall_score, and synthesis.
    """

    # Stage 1 — Raw dimensional scoring (PE-05)
    raw_prompt = build_scoring_prompt(extracted_fields, jd_decomposed, jd_text, rag_context)
    raw_result = await call_llm(raw_prompt, SCORE_SYSTEM)
    raw_dims = raw_result.get("dimensions", [])

    if not raw_dims:
        return _empty_score()

    # Stage 2 — Adversarial critique (PE-06)
    critique_prompt = build_critique_prompt(raw_result, extracted_fields)
    critique_result = await call_llm(critique_prompt, CRITIQUE_SYSTEM)
    critiques = critique_result.get("critiques", [])

    # Blend scores: 60% raw + 40% critique adjusted
    final_dims = []
    critique_map = {c["dimension"]: c for c in critiques}
    for dim in raw_dims:
        name = dim.get("dimension", "")
        raw_score = float(dim.get("score", 5))
        critique = critique_map.get(name, {})
        adjusted = float(critique.get("adjusted_score", raw_score))
        blended = round(raw_score * 0.6 + adjusted * 0.4, 1)
        final_dims.append({
            "dimension": name,
            "score": blended,
            "evidence": dim.get("evidence", []),
            "gaps": dim.get("gaps", []),
            "raw_score": raw_score,
            "critique_note": critique.get("critique", ""),
        })

    # Overall score = average of dimensions, weighted toward technical skills
    weights = {
        "Technical Skills": 1.4,
        "Experience Depth": 1.1,
        "Domain Relevance": 1.0,
        "Career Trajectory": 0.9,
    }
    total_weight = 0.0
    weighted_sum = 0.0
    for dim in final_dims:
        w = weights.get(dim["dimension"], 1.0)
        weighted_sum += dim["score"] * w
        total_weight += w

    overall = round(weighted_sum / total_weight, 1) if total_weight > 0 else 5.0

    # Stage 3 — Synthesis (PE-07)
    synth_prompt = build_synthesis_prompt(final_dims, overall, jd_text, extracted_fields)
    synth_result = await call_llm(synth_prompt, SYNTH_SYSTEM)

    return {
        "raw_scores": {"dimensions": raw_dims},
        "critique": critique_result,
        "dimensional_scores": final_dims,
        "overall_score": overall,
        "strengths": synth_result.get("strengths", []),
        "concerns": synth_result.get("concerns", []),
        "recruiter_summary": synth_result.get("recruiter_summary", ""),
        "recommendation": synth_result.get("recommendation", "maybe"),
        "suggested_questions": synth_result.get("suggested_questions", []),
        "confidence": synth_result.get("confidence", "medium"),
    }


def _empty_score() -> dict:
    return {
        "raw_scores": {},
        "critique": {},
        "dimensional_scores": [],
        "overall_score": 0.0,
        "strengths": [],
        "concerns": [],
        "recruiter_summary": "Unable to generate score — insufficient data extracted from resume.",
        "recommendation": "maybe",
        "suggested_questions": [],
        "confidence": "low",
    }
