def last_executed_query(self, cursor, sql, params):
        # https://python-oracledb.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.statement
        # The DB API definition does not define this attribute.
        statement = cursor.statement
        # Unlike Psycopg's `query` and MySQLdb`'s `_executed`, oracledb's
        # `statement` doesn't contain the query parameters. Substitute
        # parameters manually.
        if statement and params:
            if isinstance(params, (tuple, list)):
                params = {
                    f":arg{i}": param for i, param in enumerate(dict.fromkeys(params))
                }
            elif isinstance(params, dict):
                params = {f":{key}": val for (key, val) in params.items()}
            for key in sorted(params, key=len, reverse=True):
                statement = statement.replace(
                    key, force_str(params[key], errors="replace")
                )
        return (
            super().last_executed_query(cursor, sql, params)
            if statement is None
            else statement
        )