def timezone_today():
    """Return the current date in the current time zone."""
    if settings.USE_TZ:
        return timezone.localdate()
    else:
        return datetime.date.today()