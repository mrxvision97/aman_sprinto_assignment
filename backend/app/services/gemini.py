"""
Gemini API client for all LLM and embedding calls.
Handles rate limiting (15 RPM free tier) with sequential semaphore + delays.
Includes retry logic with exponential backoff.
"""
import asyncio
import json
import re
import time
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()

# Initialize Gemini
genai.configure(api_key=settings.gemini_api_key)

# Rate limiter: max 1 concurrent call, 4 sec between calls (stays under 15 RPM)
_semaphore = asyncio.Semaphore(1)
_last_call_time = 0.0
MIN_CALL_INTERVAL = 4.0  # seconds


async def _rate_limited_call(fn, *args, **kwargs):
    """Wrap any API call with rate limiting and retry logic."""
    global _last_call_time
    async with _semaphore:
        # Enforce minimum interval between calls
        elapsed = time.monotonic() - _last_call_time
        if elapsed < MIN_CALL_INTERVAL:
            await asyncio.sleep(MIN_CALL_INTERVAL - elapsed)

        for attempt in range(3):
            try:
                result = await asyncio.get_event_loop().run_in_executor(None, fn, *args, **kwargs)
                _last_call_time = time.monotonic()
                return result
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str:
                    wait = (attempt + 1) * 10
                    await asyncio.sleep(wait)
                    continue
                raise
        raise RuntimeError("Gemini API rate limit exceeded after 3 retries")


def _make_llm_call(prompt: str, system: str = "") -> str:
    """Synchronous Gemini call returning text."""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system if system else None,
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return response.text


def _make_embed_call(text: str) -> list[float]:
    """Synchronous embedding call."""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


async def call_llm(prompt: str, system: str = "") -> dict:
    """Async LLM call returning parsed JSON dict."""
    raw = await _rate_limited_call(_make_llm_call, prompt, system)
    return _parse_json(raw)


async def embed_text(text: str) -> list[float]:
    """Async embedding call returning 768-dim vector."""
    return await _rate_limited_call(_make_embed_call, text)


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {}
