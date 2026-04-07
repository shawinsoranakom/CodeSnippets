def convert_textfield_value(self, value, expression, connection):
        if isinstance(value, Database.LOB):
            value = value.read()
        return value