def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, (list, tuple)):
            return [
                self.base_field.get_db_prep_value(i, connection, prepared=False)
                for i in value
            ]
        return value