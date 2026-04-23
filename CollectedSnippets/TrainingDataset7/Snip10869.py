def as_sql(self, compiler, connection):
        value = self.output_field.get_db_prep_value(self.value, connection)
        if value is None:
            value = "null"
        return "%s", (value,)