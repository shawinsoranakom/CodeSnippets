def _start_transaction_under_autocommit(self):
        """
        Start a transaction explicitly in autocommit mode.

        Staying in autocommit mode works around a bug of sqlite3 that breaks
        savepoints when autocommit is disabled.
        """
        if self.transaction_mode is None:
            self.cursor().execute("BEGIN")
        else:
            self.cursor().execute(f"BEGIN {self.transaction_mode}")