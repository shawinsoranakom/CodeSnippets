def _coerce(val: str) -> Any:
    """Best-effort type coercion from string to Python types."""
    low = val.lower()
    if low == "null":
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    # integers
    if re.fullmatch(r"[+-]?\d+", val):
        try:
            return int(val)
        except ValueError:
            pass
    # floats (keep 'inf'/'-inf'/'nan' as strings)
    if re.fullmatch(r"[+-]?\d*\.\d+", val):
        try:
            return float(val)
        except ValueError:
            pass
    return val