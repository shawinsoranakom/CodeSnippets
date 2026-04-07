def _close(self):
        if self.connection is not None:
            with self.wrap_database_errors:
                return self.connection.close()