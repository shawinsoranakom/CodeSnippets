def do_timezone(value, arg):
    """
    Convert a datetime to local time in a given time zone.

    The argument must be an instance of a tzinfo subclass or a time zone name.

    Naive datetimes are assumed to be in local time in the default time zone.
    """
    if not isinstance(value, datetime):
        return ""

    # Obtain a timezone-aware datetime
    try:
        if timezone.is_naive(value):
            default_timezone = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_timezone)
    # Filters must never raise exceptionsm, so catch everything.
    except Exception:
        return ""

    # Obtain a tzinfo instance
    if isinstance(arg, tzinfo):
        tz = arg
    elif isinstance(arg, str):
        try:
            tz = zoneinfo.ZoneInfo(arg)
        except zoneinfo.ZoneInfoNotFoundError:
            return ""
    else:
        return ""

    result = timezone.localtime(value, tz)

    # HACK: the convert_to_local_time flag will prevent
    #       automatic conversion of the value to local time.
    result = datetimeobject(
        result.year,
        result.month,
        result.day,
        result.hour,
        result.minute,
        result.second,
        result.microsecond,
        result.tzinfo,
    )
    result.convert_to_local_time = False
    return result