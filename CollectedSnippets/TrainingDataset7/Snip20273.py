def get_db_prep_save(self, value, connection):
        if not value:
            return
        if isinstance(value, MyWrapper):
            return str(value)
        return value