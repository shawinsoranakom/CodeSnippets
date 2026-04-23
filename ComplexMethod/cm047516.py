def _expression_property_getter(self, property_name: str) -> Callable[[T], typing.Any]:
        """ Return a function that maps a field value (date or datetime) to the
        given ``property_name``.
        """
        match property_name:
            case 'tz':
                return lambda value: value
            case 'year_number':
                return lambda value: value.year
            case 'quarter_number':
                return lambda value: value.month // 4 + 1
            case 'month_number':
                return lambda value: value.month
            case 'iso_week_number':
                return lambda value: value.isocalendar().week
            case 'day_of_year':
                return lambda value: value.timetuple().tm_yday
            case 'day_of_month':
                return lambda value: value.day
            case 'day_of_week':
                return lambda value: value.timetuple().tm_wday
            case 'hour_number' if self.type == 'datetime':
                return lambda value: value.hour
            case 'minute_number' if self.type == 'datetime':
                return lambda value: value.minute
            case 'second_number' if self.type == 'datetime':
                return lambda value: value.second
            case 'hour_number' | 'minute_number' | 'second_number':
                # for dates, it is always 0
                return lambda value: 0
        assert property_name not in READ_GROUP_NUMBER_GRANULARITY, f"Property not implemented {property_name}"
        raise ValueError(
            f"Error when processing the granularity {property_name} is not supported. "
            f"Only {', '.join(READ_GROUP_NUMBER_GRANULARITY.keys())} are supported"
        )