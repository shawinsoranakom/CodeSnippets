def _commit(self):
        if self.connection is not None:
            with debug_transaction(self, "COMMIT"), self.wrap_database_errors:
                return self.connection.commit()