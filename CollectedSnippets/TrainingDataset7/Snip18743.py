def test_parameter_count_exceeds_variable_or_column_limit(self):
        sql = "SELECT MAX(%s)" % ", ".join(["%s"] * 1001)
        params = list(range(1001))
        for label, limit, current_limit in [
            (
                "variable",
                sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER,
                connection.features.max_query_params,
            ),
            (
                "column",
                sqlite3.SQLITE_LIMIT_COLUMN,
                connection.connection.getlimit(sqlite3.SQLITE_LIMIT_COLUMN),
            ),
        ]:
            with self.subTest(limit=label):
                connection.connection.setlimit(limit, 1000)
                self.addCleanup(connection.connection.setlimit, limit, current_limit)
                with connection.cursor() as cursor:
                    # This should not raise an exception.
                    cursor.db.ops.last_executed_query(cursor.cursor, sql, params)
                connection.connection.setlimit(limit, current_limit)