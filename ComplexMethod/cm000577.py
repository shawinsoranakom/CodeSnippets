def _parse_boolean_response(response_text: str) -> tuple[bool, str | None]:
    """Parse an LLM response into a boolean result.

    Returns a ``(result, error)`` tuple.  *error* is ``None`` when the
    response is unambiguous; otherwise it contains a diagnostic message
    and *result* defaults to ``False``.
    """
    text = response_text.strip().lower()
    if text == "true":
        return True, None
    if text == "false":
        return False, None

    # Fuzzy match – use word boundaries to avoid false positives like "untrue".
    tokens = set(re.findall(r"\b(true|false|yes|no|1|0)\b", text))
    if tokens == {"true"} or tokens == {"yes"} or tokens == {"1"}:
        return True, None
    if tokens == {"false"} or tokens == {"no"} or tokens == {"0"}:
        return False, None

    return False, f"Unclear AI response: '{response_text}'"