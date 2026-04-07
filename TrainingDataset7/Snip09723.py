def convert_empty_bytes(value, expression, connection):
        return b"" if value is None else value