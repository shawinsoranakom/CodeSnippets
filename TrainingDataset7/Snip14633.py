def get_default_timezone():
    """
    Return the default time zone as a tzinfo instance.

    This is the time zone defined by settings.TIME_ZONE.
    """
    return zoneinfo.ZoneInfo(settings.TIME_ZONE)