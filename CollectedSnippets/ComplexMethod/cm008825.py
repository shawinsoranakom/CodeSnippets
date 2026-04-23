def datetime_from_str(date_str, precision='auto', format='%Y%m%d'):
    R"""
    Return a datetime object from a string.
    Supported format:
        (now|today|yesterday|DATE)([+-]\d+(microsecond|second|minute|hour|day|week|month|year)s?)?

    @param format       strftime format of DATE
    @param precision    Round the datetime object: auto|microsecond|second|minute|hour|day
                        auto: round to the unit provided in date_str (if applicable).
    """
    auto_precision = False
    if precision == 'auto':
        auto_precision = True
        precision = 'microsecond'
    today = datetime_round(dt.datetime.now(dt.timezone.utc), precision)
    if date_str in ('now', 'today'):
        return today
    if date_str == 'yesterday':
        return today - dt.timedelta(days=1)
    match = re.match(
        r'(?P<start>.+)(?P<sign>[+-])(?P<time>\d+)(?P<unit>microsecond|second|minute|hour|day|week|month|year)s?',
        date_str)
    if match is not None:
        start_time = datetime_from_str(match.group('start'), precision, format)
        time = int(match.group('time')) * (-1 if match.group('sign') == '-' else 1)
        unit = match.group('unit')
        if unit == 'month' or unit == 'year':
            new_date = datetime_add_months(start_time, time * 12 if unit == 'year' else time)
            unit = 'day'
        else:
            if unit == 'week':
                unit = 'day'
                time *= 7
            delta = dt.timedelta(**{unit + 's': time})
            new_date = start_time + delta
        if auto_precision:
            return datetime_round(new_date, unit)
        return new_date

    return datetime_round(dt.datetime.strptime(date_str, format), precision)