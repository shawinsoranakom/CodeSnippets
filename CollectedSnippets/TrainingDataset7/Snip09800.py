def pg_version(self):
        with self.temporary_connection():
            return self.connection.info.server_version