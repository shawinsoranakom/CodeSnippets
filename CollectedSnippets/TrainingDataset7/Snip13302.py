def first(value):
    """Return the first item in a list."""
    try:
        return value[0]
    except IndexError:
        return ""