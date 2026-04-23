def get_default_timezone_name():
    """Return the name of the default time zone."""
    return _get_timezone_name(get_default_timezone())