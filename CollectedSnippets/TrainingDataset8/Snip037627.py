def from_raw_values(
        cls,
        value: DateValue,
        min_value: SingleDateValue,
        max_value: SingleDateValue,
    ) -> "_DateInputValues":

        parsed_value, is_range = _parse_date_value(value=value)
        return cls(
            value=parsed_value,
            is_range=is_range,
            min=_parse_min_date(
                min_value=min_value,
                parsed_dates=parsed_value,
            ),
            max=_parse_max_date(
                max_value=max_value,
                parsed_dates=parsed_value,
            ),
        )