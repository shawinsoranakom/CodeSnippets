def extract_error_detail(response_text: str) -> str:
    """Extract a human-readable error detail from a ClientAPIException response.

    The response body may contain a ``detail`` value that is a string, a dict
    with a ``msg`` key, or a list of such dicts.  This helper normalises all
    three shapes into a single value suitable for inclusion in an error message.
    """
    fallback = response_text or "<empty response body>"
    try:
        payload = json.loads(response_text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback

    detail = payload.get("detail")
    if detail in (None, "", [], {}):
        for field in ("message", "details", "error"):
            detail = payload.get(field)
            if detail not in (None, "", [], {}):
                break
        else:
            return fallback

    if isinstance(detail, list):
        detail = detail[0] if detail else None
    if isinstance(detail, dict):
        detail = detail.get("msg") or detail

    return str(detail) if detail not in (None, "", [], {}) else fallback