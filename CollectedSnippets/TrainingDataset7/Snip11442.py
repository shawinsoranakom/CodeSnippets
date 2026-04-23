def get_db_prep_save(self, value, connection):
        if value is None or (
            value == ""
            and (
                not self.target_field.empty_strings_allowed
                or connection.features.interprets_empty_strings_as_nulls
            )
        ):
            return None
        else:
            return self.target_field.get_db_prep_save(value, connection=connection)