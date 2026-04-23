def parse_date(value: str, env: Environment) -> date | datetime:
    r""" Parse a technical date string into a date or datetime.

    This supports ISO formatted dates and dates relative to now.
    `parse_iso_date` is used if the input starts with r'\d+-'.
    Otherwise, the date is computed by starting from now at user's timezone.
    We can also start 'today' (resulting in a date type). Then we apply offsets:

    - we can add 'd', 'w', 'm', 'y', 'H', 'M', 'S':
      days, weeks, months, years, hours, minutes, seconds
      - "+3d" to add 3 days
      - "-1m" to subtract one month
    - we can set a part of the date which will reset to midnight or only lower
      date parts
      - "=1d" sets first day of month at midnight
      - "=6m" sets June and resets to midnight
      - "=3H" sets time to 3:00:00
    - weekdays are handled similarly
      - "=tuesday" sets to Tuesday of the current week at midnight
      - "+monday" goes to next Monday (no change if we are on Monday)
      - "=week_start" sets to the first day of the current week, according to the locale

    The DSL for relative dates is as follows:
    ```
    relative_date := ('today' | 'now')? offset*
    offset := date_rel | time_rel | weekday
    date_rel := (regex) [=+-]\d+[dwmy]
    time_rel := (regex) [=+-]\d+[HMS]
    weekday := [=+-] ('monday' | ... | 'sunday' | 'week_start')
    ```

    An equivalent function is JavaScript is `parseSmartDateInput`.

    :param value: The string to parse
    :param env: The environment to get the current date (in user's tz)
    :param naive: Whether to cast the result to a naive datetime.
    """
    if re.match(r'\d+-', value):
        return parse_iso_date(value)
    terms = value.split()
    if not terms:
        raise ValueError("Empty date value")

    # Find the starting point
    from odoo.orm.fields_temporal import Date, Datetime  # noqa: PLC0415

    dt: datetime | date = Datetime.now()
    term = terms.pop(0) if terms[0] in ('today', 'now') else 'now'
    if term == 'today':
        dt = Date.context_today(env['base'], dt)
    else:
        dt = Datetime.context_timestamp(env['base'], dt)

    for term in terms:
        operator = term[0]
        if operator not in ('+', '-', '=') or len(term) < 3:
            raise ValueError(f"Invalid term {term!r} in expression date: {value!r}")

        # Weekday
        dayname = term[1:]
        if dayname in WEEKDAY_NUMBER or dayname == "week_start":
            week_start = int(env["res.lang"]._get_data(code=env.user.lang).week_start) - 1
            weekday = week_start if dayname == "week_start" else WEEKDAY_NUMBER[dayname]
            weekday_offset = ((weekday - week_start) % 7) - ((dt.weekday() - week_start) % 7)
            if operator in ('+', '-'):
                if operator == '+' and weekday_offset < 0:
                    weekday_offset += 7
                elif operator == '-' and weekday_offset > 0:
                    weekday_offset -= 7
            elif isinstance(dt, datetime):
                dt += TRUNCATE_TODAY
            dt += timedelta(weekday_offset)
            continue

        # Operations on dates
        try:
            unit = _SHORT_DATE_UNIT[term[-1]]
            if operator in ('+', '-'):
                number = int(term[:-1])  # positive or negative
            else:
                number = int(term[1:-1])
                unit = unit.removesuffix('s')
                if isinstance(dt, datetime):
                    dt += TRUNCATE_UNIT[unit]
                # note: '=Nw' is not supported
            dt += relativedelta(**{unit: number})
        except (ValueError, TypeError, KeyError):
            raise ValueError(f"Invalid term {term!r} in expression date: {value!r}")

    # always return a naive date
    if isinstance(dt, datetime) and dt.tzinfo is not None:
        dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
    return dt