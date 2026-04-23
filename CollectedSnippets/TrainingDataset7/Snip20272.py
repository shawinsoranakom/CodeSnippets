def from_db_value(self, value, expression, connection):
        if not value:
            return
        return MyWrapper(value)