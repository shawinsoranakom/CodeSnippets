def get_db_prep_save(self, value, connection):
        return str(value.title)