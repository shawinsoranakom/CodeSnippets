def _parse_min_date(
    min_value: SingleDateValue,
    parsed_dates: Sequence[date],
) -> date:
    parsed_min_date: date
    if isinstance(min_value, datetime):
        parsed_min_date = min_value.date()
    elif isinstance(min_value, date):
        parsed_min_date = min_value
    elif min_value is None:
        if parsed_dates:
            parsed_min_date = parsed_dates[0] - relativedelta.relativedelta(years=10)
        else:
            parsed_min_date = date.today() - relativedelta.relativedelta(years=10)
    else:
        raise StreamlitAPIException(
            "DateInput min should either be a date/datetime or None"
        )
    return parsed_min_date