def adapt_timefield_value(self, value):
        """
        Transform a time value to an object compatible with what is expected
        by the backend driver for time columns.
        """
        if value is None:
            return None
        if timezone.is_aware(value):
            raise ValueError("Django does not support timezone-aware times.")
        return str(value)