def safe_int_tokens(value: Any) -> int:
    """Safely coerce a token count value to int, returning 0 on failure.

    Handles the full range of representations that LLM providers store in span
    attributes: plain ``int``, ``float`` (e.g. ``12.0``), decimal strings
    (``"12"``), float strings (``"12.0"``), and scientific notation (``"1e3"``).

    Returns 0 for ``None``, ``"NaN"``, ``"inf"``, empty strings, booleans
    stored as strings, and any other non-numeric value.

    Args:
        value: Raw token count from a span attribute.

    Returns:
        Non-negative integer token count, or 0 if the value cannot be parsed.
    """
    if isinstance(value, bool):
        # bool is a subclass of int; treat True/False as invalid token counts.
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) else 0
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                parsed = float(value)
                return int(parsed) if math.isfinite(parsed) else 0
            except (ValueError, TypeError, OverflowError):
                return 0
    return 0