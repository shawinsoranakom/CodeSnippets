def is_postgresql_17(self):
        return self.connection.pg_version >= 170000