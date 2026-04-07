def _from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return [
            self.base_field.from_db_value(item, expression, connection)
            for item in value
        ]