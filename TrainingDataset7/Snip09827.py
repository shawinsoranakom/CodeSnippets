def is_postgresql_18(self):
        return self.connection.pg_version >= 180000