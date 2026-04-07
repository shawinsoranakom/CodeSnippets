def last(value):
    """Return the last item in a list."""
    try:
        return value[-1]
    except IndexError:
        return ""