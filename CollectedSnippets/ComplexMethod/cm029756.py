def fromisoformat(cls, date_string):
        """Construct a datetime from a string in one of the ISO 8601 formats."""
        if not isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')

        if len(date_string) < 7:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

        # Split this at the separator
        try:
            separator_location = _find_isoformat_datetime_separator(date_string)
            dstr = date_string[0:separator_location]
            tstr = date_string[(separator_location+1):]

            date_components = _parse_isoformat_date(dstr)
        except ValueError:
            raise ValueError(
                f'Invalid isoformat string: {date_string!r}') from None

        if tstr:
            try:
                (time_components,
                 became_next_day,
                 error_from_components,
                 error_from_tz) = _parse_isoformat_time(tstr)
            except ValueError:
                raise ValueError(
                    f'Invalid isoformat string: {date_string!r}') from None
            else:
                if error_from_tz:
                    raise error_from_tz
                if error_from_components:
                    raise ValueError("minute, second, and microsecond must be 0 when hour is 24")

                if became_next_day:
                    year, month, day = date_components
                    # Only wrap day/month when it was previously valid
                    if month <= 12 and day <= (days_in_month := _days_in_month(year, month)):
                        # Calculate midnight of the next day
                        day += 1
                        if day > days_in_month:
                            day = 1
                            month += 1
                            if month > 12:
                                month = 1
                                year += 1
                        date_components = [year, month, day]
        else:
            time_components = [0, 0, 0, 0, None]

        return cls(*(date_components + time_components))