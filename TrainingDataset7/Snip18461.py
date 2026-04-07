def call_executemany(self, connection, params=None):
        # executemany() must use an update query. Make sure it does nothing
        # by putting a false condition in the WHERE clause.
        sql = "DELETE FROM {} WHERE 0=1 AND 0=%s".format(Square._meta.db_table)
        if params is None:
            params = [(i,) for i in range(3)]
        with connection.cursor() as cursor:
            cursor.executemany(sql, params)