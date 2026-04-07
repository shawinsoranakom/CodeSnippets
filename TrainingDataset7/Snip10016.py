def adapt_timefield_value(self, value):
        if value is None:
            return None

        # SQLite doesn't support tz-aware datetimes
        if timezone.is_aware(value):
            raise ValueError("SQLite backend does not support timezone-aware times.")

        return str(value)