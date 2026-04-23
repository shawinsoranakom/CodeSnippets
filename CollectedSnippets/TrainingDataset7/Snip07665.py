def get_db_prep_save(self, value, connection):
        if isinstance(value, (list, tuple)):
            return [self.base_field.get_db_prep_save(i, connection) for i in value]
        return value