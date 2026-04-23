def _needs_quoting(value: str) -> bool:
    """Check if a value needs to be quoted in .env format."""
    if not value:
        return False
    # Quote if contains spaces, special chars, or starts/ends with whitespace
    if " " in value or "\t" in value:
        return True
    if value[0].isspace() or value[-1].isspace():
        return True
    if any(c in value for c in ["#", "'", '"', "\\", "\n", "\r"]):
        return True
    return False