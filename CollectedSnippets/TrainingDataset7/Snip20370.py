def truncate_to(value, kind, tzinfo=None):
    # Convert to target timezone before truncation
    if tzinfo is not None:
        value = value.astimezone(tzinfo)

    def truncate(value, kind):
        if kind == "second":
            return value.replace(microsecond=0)
        if kind == "minute":
            return value.replace(second=0, microsecond=0)
        if kind == "hour":
            return value.replace(minute=0, second=0, microsecond=0)
        if kind == "day":
            if isinstance(value, datetime.datetime):
                return value.replace(hour=0, minute=0, second=0, microsecond=0)
            return value
        if kind == "week":
            if isinstance(value, datetime.datetime):
                return (value - datetime.timedelta(days=value.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            return value - datetime.timedelta(days=value.weekday())
        if kind == "month":
            if isinstance(value, datetime.datetime):
                return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return value.replace(day=1)
        if kind == "quarter":
            month_in_quarter = value.month - (value.month - 1) % 3
            if isinstance(value, datetime.datetime):
                return value.replace(
                    month=month_in_quarter,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            return value.replace(month=month_in_quarter, day=1)
        # otherwise, truncate to year
        if isinstance(value, datetime.datetime):
            return value.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        return value.replace(month=1, day=1)

    value = truncate(value, kind)
    if tzinfo is not None:
        # If there was a daylight saving transition, then reset the timezone.
        value = timezone.make_aware(value.replace(tzinfo=None), tzinfo)
    return value