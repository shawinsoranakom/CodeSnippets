def end_of(value: D, granularity: Granularity) -> D:
    """
    Get end of a time period from a date or a datetime.

    :param value: initial date or datetime.
    :param granularity: Type of period in string, can be year, quarter, month, week, day or hour.
    :return: A date/datetime object corresponding to the start of the specified period.
    """
    is_datetime = isinstance(value, datetime)
    if granularity == "year":
        result = value.replace(month=12, day=31)
    elif granularity == "quarter":
        # Q1 = Mar 31st
        # Q2 = Jun 30th
        # Q3 = Sep 30th
        # Q4 = Dec 31st
        result = get_quarter(value)[1]
    elif granularity == "month":
        result = value + relativedelta(day=1, months=1, days=-1)
    elif granularity == 'week':
        # `calendar.weekday` uses ISO8601 for start of week reference, this means that
        # by default MONDAY is the first day of the week and SUNDAY is the last.
        result = value + relativedelta(days=6 - calendar.weekday(value.year, value.month, value.day))
    elif granularity == "day":
        result = value
    elif granularity == "hour" and is_datetime:
        return datetime.combine(value, time.max).replace(hour=value.hour)
    elif is_datetime:
        raise ValueError(
            "Granularity must be year, quarter, month, week, day or hour for value %s" % value
        )
    else:
        raise ValueError(
            "Granularity must be year, quarter, month, week or day for value %s" % value
        )

    return datetime.combine(result, time.max) if is_datetime else result