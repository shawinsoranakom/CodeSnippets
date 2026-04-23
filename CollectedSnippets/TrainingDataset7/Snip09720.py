def convert_timefield_value(self, value, expression, connection):
        if isinstance(value, datetime.datetime):
            value = value.time()
        return value