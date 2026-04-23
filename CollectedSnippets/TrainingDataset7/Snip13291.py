def escape_filter(value):
    """Mark the value as a string that should be auto-escaped."""
    return conditional_escape(value)