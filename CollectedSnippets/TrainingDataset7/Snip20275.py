def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return MyWrapper(value)