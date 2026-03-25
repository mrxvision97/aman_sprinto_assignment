"""PE-08: AI authorship signal detection."""
from app.services.gemini import call_llm
from app.prompts.ai_authorship import SYSTEM, build_authorship_prompt


async def detect_ai_authorship(resume_text: str) -> str:
    """Return authorship signal: none | weak | moderate | strong."""
    try:
        prompt = build_authorship_prompt(resume_text)
        result = await call_llm(prompt, SYSTEM)
        signal = result.get("signal", "none")
        return signal if signal in ("none", "weak", "moderate", "strong") else "none"
    except Exception:
        return "none"
