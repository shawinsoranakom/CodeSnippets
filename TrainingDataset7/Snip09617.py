def _commit(self):
        if self.connection is not None:
            with debug_transaction(self, "COMMIT"), wrap_oracle_errors():
                return self.connection.commit()