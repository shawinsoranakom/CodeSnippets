def adapt_timefield_value(self, value):
        if value is None:
            return None

        if isinstance(value, str):
            return datetime.datetime.strptime(value, "%H:%M:%S")

        # Oracle doesn't support tz-aware times
        if timezone.is_aware(value):
            raise ValueError("Oracle backend does not support timezone-aware times.")

        return Oracle_datetime(
            1900, 1, 1, value.hour, value.minute, value.second, value.microsecond
        )