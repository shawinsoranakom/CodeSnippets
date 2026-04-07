def ensure_connection(self):
        """Guarantee that a connection to the database is established."""
        if self.connection is None:
            if self.in_atomic_block and self.closed_in_transaction:
                raise ProgrammingError(
                    "Cannot open a new connection in an atomic block."
                )
            with self.wrap_database_errors:
                self.connect()