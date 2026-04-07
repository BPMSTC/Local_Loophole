from __future__ import annotations

import re


TAG_FLAGS = re.IGNORECASE | re.DOTALL


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_tag(text: str, tag: str) -> str | None:
    cleaned = strip_code_fences(text)
    full_match = re.search(rf"<\s*{tag}\s*>(.*?)</\s*{tag}\s*>", cleaned, TAG_FLAGS)
    if full_match:
        value = full_match.group(1).strip()
        return value or None

    open_match = re.search(rf"<\s*{tag}\s*>", cleaned, TAG_FLAGS)
    if not open_match:
        return None

    remainder = cleaned[open_match.end():]
    next_tag_match = re.search(r"\n\s*<\s*[a-zA-Z0-9_:-]+\s*>", remainder, TAG_FLAGS)
    value = remainder[: next_tag_match.start()] if next_tag_match else remainder
    value = value.strip()
    return value or None


def extract_all_tags(text: str, tag: str) -> list[str]:
    cleaned = strip_code_fences(text)
    matches = re.findall(rf"<\s*{tag}\s*>(.*?)</\s*{tag}\s*>", cleaned, TAG_FLAGS)
    return [match.strip() for match in matches if match.strip()]


def parse_choice_tag(text: str, tag: str, allowed: set[str]) -> str | None:
    value = extract_tag(text, tag)
    if value:
        normalized = _normalize_token(value)
        if normalized in allowed:
            return normalized

    normalized_text = _normalize_token(strip_code_fences(text))
    for choice in allowed:
        if re.search(rf"\b{re.escape(choice)}\b", normalized_text):
            return choice
    return None


def parse_bool_tag(text: str, tag: str) -> bool | None:
    value = extract_tag(text, tag)
    if value is None:
        return None

    normalized = _normalize_token(value)
    truthy = {"true", "yes", "pass", "passes", "passed"}
    falsy = {"false", "no", "fail", "fails", "failed"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    return None


def parse_scenarios(text: str) -> list[tuple[str, str]]:
    cleaned = strip_code_fences(text)
    scenarios: list[tuple[str, str]] = []

    blocks = re.findall(r"<\s*scenario\s*>(.*?)</\s*scenario\s*>", cleaned, TAG_FLAGS)
    for block in blocks:
        description = extract_tag(block, "description")
        explanation = extract_tag(block, "explanation")
        if description and explanation:
            scenarios.append((description, explanation))

    if scenarios:
        return scenarios

    descriptions = extract_all_tags(cleaned, "description")
    explanations = extract_all_tags(cleaned, "explanation")
    if descriptions and explanations:
        return list(zip(descriptions, explanations, strict=False))

    return []


def _normalize_token(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())