def convert_booleanfield_value(self, value, expression, connection):
        if value in (0, 1):
            value = bool(value)
        return value