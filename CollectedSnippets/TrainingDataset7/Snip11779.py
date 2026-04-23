def get_db_prep_lookup(self, value, connection):
        return ("%s", (value,))