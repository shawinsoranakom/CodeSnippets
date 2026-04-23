def _quote_params_for_last_executed_query(self, params):
        """
        Only for last_executed_query! Don't use this to execute SQL queries!
        """
        connection = self.connection.connection
        variable_limit = self.connection.features.max_query_params
        column_limit = connection.getlimit(sqlite3.SQLITE_LIMIT_COLUMN)
        batch_size = min(variable_limit, column_limit)

        if len(params) > batch_size:
            results = ()
            for index in range(0, len(params), batch_size):
                chunk = params[index : index + batch_size]
                results += self._quote_params_for_last_executed_query(chunk)
            return results

        sql = "SELECT " + ", ".join(["QUOTE(?)"] * len(params))
        # Bypass Django's wrappers and use the underlying sqlite3 connection
        # to avoid logging this query - it would trigger infinite recursion.
        cursor = self.connection.connection.cursor()
        # Native sqlite3 cursors cannot be used as context managers.
        try:
            return cursor.execute(sql, params).fetchone()
        finally:
            cursor.close()