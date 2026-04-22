def _parse_max_date(
    max_value: SingleDateValue,
    parsed_dates: Sequence[date],
) -> date:
    parsed_max_date: date
    if isinstance(max_value, datetime):
        parsed_max_date = max_value.date()
    elif isinstance(max_value, date):
        parsed_max_date = max_value
    elif max_value is None:
        if parsed_dates:
            parsed_max_date = parsed_dates[-1] + relativedelta.relativedelta(years=10)
        else:
            parsed_max_date = date.today() + relativedelta.relativedelta(years=10)
    else:
        raise StreamlitAPIException(
            "DateInput max should either be a date/datetime or None"
        )
    return parsed_max_date