def get_db_prep_value(self, value, connection, prepared=False):
        if not value:
            return
        if isinstance(value, MyWrapper):
            return str(value)
        return value