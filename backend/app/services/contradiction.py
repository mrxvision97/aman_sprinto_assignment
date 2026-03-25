"""Deterministic contradiction detection in extracted resume fields."""
from datetime import datetime


def check_contradictions(extracted_fields: dict) -> list[dict]:
    """Run deterministic checks for internal resume inconsistencies."""
    flags = []

    # Extract relevant values
    experience_years = _get_num(extracted_fields, "total_experience_years")
    education = _get_str(extracted_fields, "education")
    summary = _get_str(extracted_fields, "summary")

    current_year = datetime.now().year

    # Check 1: Experience years vs graduation year
    if experience_years and education:
        grad_year = _extract_year(education)
        if grad_year:
            max_possible = current_year - grad_year
            if experience_years > max_possible + 2:  # +2 for pre-graduation internships
                flags.append({
                    "type": "experience_exceeds_graduation",
                    "description": (
                        f"Claims {experience_years:.0f} years of experience but graduated ~{grad_year} "
                        f"({max_possible} years ago). Claimed experience may be overstated."
                    ),
                    "severity": "warning",
                })

    # Check 2: Summary claims vs calculated experience
    if summary and experience_years:
        claimed_in_summary = _extract_years_claim(summary)
        if claimed_in_summary and abs(claimed_in_summary - experience_years) > 3:
            flags.append({
                "type": "experience_claim_mismatch",
                "description": (
                    f"Summary claims '{claimed_in_summary:.0f} years' but calculated experience "
                    f"is {experience_years:.0f} years. Verify with candidate."
                ),
                "severity": "info",
            })

    return flags


def _get_num(fields: dict, key: str) -> float | None:
    val = fields.get(key, {})
    if isinstance(val, dict):
        v = val.get("value")
    else:
        v = val
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _get_str(fields: dict, key: str) -> str | None:
    val = fields.get(key, {})
    if isinstance(val, dict):
        v = val.get("value")
    else:
        v = val
    return str(v) if v else None


def _extract_year(text: str) -> int | None:
    """Extract the most recent graduation year from education text."""
    import re
    years = re.findall(r"\b(19[8-9]\d|20[0-2]\d)\b", text)
    if years:
        return max(int(y) for y in years)
    return None


def _extract_years_claim(text: str) -> float | None:
    """Extract years of experience claimed in summary text."""
    import re
    match = re.search(r"(\d+)\+?\s+years?\s+of\s+(?:professional\s+)?experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None
