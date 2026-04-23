def safe(value):
    """Mark the value as a string that should not be auto-escaped."""
    return mark_safe(value)