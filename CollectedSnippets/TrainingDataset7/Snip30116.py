def get_db_prep_value(self, value, connection, prepared=False):
            # Use prepared=False to ensure str -> UUID conversion is performed.
            return super().get_db_prep_value(value, connection, prepared=False)