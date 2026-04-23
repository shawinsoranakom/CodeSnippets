def _format_answer(value: object) -> str:
    """Convert an answer value (str, list, dict, None) to a human-readable string."""
    if value is None:
        return "(no answer)"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        parts = [f"{k}: {v}" for k, v in value.items() if v]
        return "; ".join(parts) if parts else "(no answer)"
    return str(value)