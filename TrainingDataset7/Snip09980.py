def max_query_params(self):
        """
        SQLite has a variable limit per query. The limit can be changed using
        the SQLITE_MAX_VARIABLE_NUMBER compile-time option (which defaults to
        32766) or lowered per connection at run-time with
        setlimit(SQLITE_LIMIT_VARIABLE_NUMBER, N).
        """
        self.connection.ensure_connection()
        return self.connection.connection.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)