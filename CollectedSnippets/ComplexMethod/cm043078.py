def to_int(value, default=0):
    """Coerce incoming values to integers, falling back to default."""
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default

        match = re.match(r"^-?\d+", stripped)
        if match:
            try:
                return int(match.group())
            except ValueError:
                return default
    return default