def convert_datefield_value(self, value, expression, connection):
        if isinstance(value, datetime.datetime):
            value = value.date()
        return value