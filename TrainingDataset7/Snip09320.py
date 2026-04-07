def adapt_durationfield_value(self, value):
        """
        Transform a timedelta value into an object compatible with what is
        expected by the backend driver for duration columns (by default,
        an integer of microseconds).
        """
        if value is None:
            return None
        return duration_microseconds(value)