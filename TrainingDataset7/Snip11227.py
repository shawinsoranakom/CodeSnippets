def get_db_prep_value(self, value, connection, prepared=False):
        return value if prepared else self.get_prep_value(value)