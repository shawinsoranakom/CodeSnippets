def convert_durationfield_value(self, value, expression, connection):
        if value is not None:
            return datetime.timedelta(0, 0, value)