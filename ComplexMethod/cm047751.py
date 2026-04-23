def date_range(start: D, end: D, step: relativedelta = relativedelta(months=1)) -> Iterator[datetime]:
    """Date range generator with a step interval.

    :param start: beginning date of the range.
    :param end: ending date of the range (inclusive).
    :param step: interval of the range (positive).
    :return: a range of datetime from start to end.
    """

    post_process = lambda dt: dt  # noqa: E731
    if isinstance(start, datetime) and isinstance(end, datetime):
        are_naive = start.tzinfo is None and end.tzinfo is None
        are_utc = start.tzinfo == pytz.utc and end.tzinfo == pytz.utc

        # Cases with miscellenous timezone are more complexe because of DST.
        are_others = start.tzinfo and end.tzinfo and not are_utc

        if are_others and start.tzinfo.zone != end.tzinfo.zone:
            raise ValueError("Timezones of start argument and end argument seem inconsistent")

        if not are_naive and not are_utc and not are_others:
            raise ValueError("Timezones of start argument and end argument mismatch")

        if not are_naive:
            post_process = start.tzinfo.localize
            start = start.replace(tzinfo=None)
            end = end.replace(tzinfo=None)

    elif isinstance(start, date) and isinstance(end, date):
        if not isinstance(start + step, date):
            raise ValueError("the step interval must add only entire days")  # noqa: TRY004
    else:
        raise ValueError("start/end should be both date or both datetime type")  # noqa: TRY004

    if start > end:
        raise ValueError("start > end, start date must be before end")

    if start >= start + step:
        raise ValueError("Looks like step is null or negative")

    while start <= end:
        yield post_process(start)
        start += step