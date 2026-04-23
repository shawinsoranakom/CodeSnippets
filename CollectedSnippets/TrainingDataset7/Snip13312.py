def time(value, arg=None):
    """Format a time according to the given format."""
    if value in (None, ""):
        return ""
    try:
        return formats.time_format(value, arg)
    except (AttributeError, TypeError):
        try:
            return time_format(value, arg)
        except (AttributeError, TypeError):
            return ""