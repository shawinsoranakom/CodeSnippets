def start_of(value: D, granularity: Granularity) -> D:
    """
    Get start of a time period from a date or a datetime.

    :param value: initial date or datetime.
    :param granularity: type of period in string, can be year, quarter, month, week, day or hour.
    :return: a date/datetime object corresponding to the start of the specified period.
    """
    is_datetime = isinstance(value, datetime)
    if granularity == "year":
        result = value.replace(month=1, day=1)
    elif granularity == "quarter":
        # Q1 = Jan 1st
        # Q2 = Apr 1st
        # Q3 = Jul 1st
        # Q4 = Oct 1st
        result = get_quarter(value)[0]
    elif granularity == "month":
        result = value.replace(day=1)
    elif granularity == 'week':
        # `calendar.weekday` uses ISO8601 for start of week reference, this means that
        # by default MONDAY is the first day of the week and SUNDAY is the last.
        result = value - relativedelta(days=calendar.weekday(value.year, value.month, value.day))
    elif granularity == "day":
        result = value
    elif granularity == "hour" and is_datetime:
        return datetime.combine(value, time.min).replace(hour=value.hour)
    elif is_datetime:
        raise ValueError(
            "Granularity must be year, quarter, month, week, day or hour for value %s" % value
        )
    else:
        raise ValueError(
            "Granularity must be year, quarter, month, week or day for value %s" % value
        )

    return datetime.combine(result, time.min) if is_datetime else result