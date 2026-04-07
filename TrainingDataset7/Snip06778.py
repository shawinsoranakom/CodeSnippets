def db_type(self, connection):
        self._check_connection(connection)
        return super().db_type(connection)