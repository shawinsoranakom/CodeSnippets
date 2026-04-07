def last_executed_query(self, cursor, sql, params):
            # https://www.psycopg.org/docs/cursor.html#cursor.query
            # The query attribute is a Psycopg extension to the DB API 2.0.
            if cursor.query is not None:
                return cursor.query.decode()
            return super().last_executed_query(cursor, sql, params)