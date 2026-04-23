def _looks_like_import_path(value: str) -> bool:
    """Return True if **value** looks like a valid Python import path or False
    otherwise."""
    if not value:
        return False
    if any(c.isspace() for c in value):
        return False
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
    )
    if any(c not in allowed_chars for c in value):
        return False
    if value[0] == "." or value[-1] == ".":
        return False
    parts = value.split(".")
    if any(part == "" for part in parts):
        return False
    return all(part.isidentifier() for part in parts)