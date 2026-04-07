def test_sqlmigrate_for_non_transactional_databases(self):
        """
        Transaction wrappers aren't shown for databases that don't support
        transactional DDL.
        """
        out = io.StringIO()
        with mock.patch.object(connection.features, "can_rollback_ddl", False):
            call_command("sqlmigrate", "migrations", "0001", stdout=out)
        output = out.getvalue().lower()
        queries = [q.strip() for q in output.splitlines()]
        start_transaction_sql = connection.ops.start_transaction_sql()
        if start_transaction_sql:
            self.assertNotIn(start_transaction_sql.lower(), queries)
        self.assertNotIn(connection.ops.end_transaction_sql().lower(), queries)