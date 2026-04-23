def length(value):
    """Return the length of the value - useful for lists."""
    try:
        return len(value)
    except (ValueError, TypeError):
        return 0