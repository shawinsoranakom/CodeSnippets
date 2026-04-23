def end_transaction_sql(self, success=True):
        """Return the SQL statement required to end a transaction."""
        if not success:
            return "ROLLBACK;"
        return "COMMIT;"