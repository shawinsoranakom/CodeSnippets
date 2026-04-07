def timeuntil_filter(value, arg=None):
    """Format a date as the time until that date (i.e. "4 days, 6 hours")."""
    if not value:
        return ""
    try:
        return timeuntil(value, arg)
    except (ValueError, TypeError):
        return ""