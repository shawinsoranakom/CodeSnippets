def cast_db_type(self, connection):
        return self.target_field.cast_db_type(connection=connection)