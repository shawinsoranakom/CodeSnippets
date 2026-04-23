def _set_autocommit(self, autocommit):
        with self.wrap_database_errors:
            self.connection.autocommit(autocommit)