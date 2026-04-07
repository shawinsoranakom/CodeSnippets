def convert_empty_strings(self, value, expression, connection):
        if (not value) and isinstance(value, str):
            return None
        return value