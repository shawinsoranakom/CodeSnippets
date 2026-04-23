def get_db_prep_value(self, value, connection, prepared=False):
        return connection.ops.adapt_durationfield_value(value)