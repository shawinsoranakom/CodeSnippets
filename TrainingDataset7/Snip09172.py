def _rollback(self):
        if self.connection is not None:
            with debug_transaction(self, "ROLLBACK"), self.wrap_database_errors:
                return self.connection.rollback()