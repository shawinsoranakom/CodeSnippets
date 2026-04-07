def now():
    """
    Return an aware or naive datetime.datetime, depending on settings.USE_TZ.
    """
    return datetime.now(tz=UTC if settings.USE_TZ else None)