def test_sqlmigrate_for_non_atomic_migration(self):
        """
        Transaction wrappers aren't shown for non-atomic migrations.
        """
        out = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001", stdout=out)
        output = out.getvalue().lower()
        queries = [q.strip() for q in output.splitlines()]
        if connection.ops.start_transaction_sql():
            self.assertNotIn(connection.ops.start_transaction_sql().lower(), queries)
        self.assertNotIn(connection.ops.end_transaction_sql().lower(), queries)