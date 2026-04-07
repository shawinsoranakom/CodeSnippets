def convert_booleanfield_value(self, value, expression, connection):
        return bool(value) if value in (1, 0) else value