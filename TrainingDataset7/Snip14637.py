def _get_timezone_name(timezone):
    """
    Return the offset for fixed offset timezones, or the name of timezone if
    not set.
    """
    return timezone.tzname(None) or str(timezone)