def get_db_prep_save(self, value, connection):
        if hasattr(value, "as_sql"):
            return value
        value = self.get_prep_value(value)
        value = connection.ops.validate_autopk_value(value)
        return self.get_db_prep_value(value, connection=connection, prepared=True)