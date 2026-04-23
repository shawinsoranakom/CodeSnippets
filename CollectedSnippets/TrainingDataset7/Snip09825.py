def is_postgresql_16(self):
        return self.connection.pg_version >= 160000