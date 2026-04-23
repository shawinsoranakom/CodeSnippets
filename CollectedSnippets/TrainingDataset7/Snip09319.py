def adapt_datetimefield_value(self, value):
        """
        Transform a datetime value to an object compatible with what is
        expected by the backend driver for datetime columns.
        """
        if value is None:
            return None
        return str(value)