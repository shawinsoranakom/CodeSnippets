def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Tag(int(value))