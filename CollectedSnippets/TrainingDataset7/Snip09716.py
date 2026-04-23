def convert_binaryfield_value(self, value, expression, connection):
        if isinstance(value, Database.LOB):
            value = force_bytes(value.read())
        return value