def get_current_timezone():
    """Return the currently active time zone as a tzinfo instance."""
    return getattr(_active, "value", get_default_timezone())