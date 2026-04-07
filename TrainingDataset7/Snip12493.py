def prepare_value(self, value):
        if isinstance(value, datetime.timedelta):
            return duration_string(value)
        return value