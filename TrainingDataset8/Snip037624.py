def _parse_date_value(value: DateValue) -> Tuple[List[date], bool]:
    parsed_dates: List[date]
    range_value: bool = False
    if value is None:
        # Set value default.
        parsed_dates = [datetime.now().date()]
    elif isinstance(value, datetime):
        parsed_dates = [value.date()]
    elif isinstance(value, date):
        parsed_dates = [value]
    elif isinstance(value, (list, tuple)):
        if not len(value) in (0, 1, 2):
            raise StreamlitAPIException(
                "DateInput value should either be an date/datetime or a list/tuple of "
                "0 - 2 date/datetime values"
            )

        parsed_dates = [v.date() if isinstance(v, datetime) else v for v in value]
        range_value = True
    else:
        raise StreamlitAPIException(
            "DateInput value should either be an date/datetime or a list/tuple of "
            "0 - 2 date/datetime values"
        )
    return parsed_dates, range_value