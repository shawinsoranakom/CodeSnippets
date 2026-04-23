def to_current_timezone(value):
    """
    When time zone support is enabled, convert aware datetimes
    to naive datetimes in the current time zone for display.
    """
    if settings.USE_TZ and value is not None and timezone.is_aware(value):
        return timezone.make_naive(value)
    return value