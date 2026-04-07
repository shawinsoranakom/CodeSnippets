def get_current_timezone_name():
    """Return the name of the currently active time zone."""
    return _get_timezone_name(get_current_timezone())