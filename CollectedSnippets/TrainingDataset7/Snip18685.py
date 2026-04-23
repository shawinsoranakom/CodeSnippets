def _select(self, val):
        with connection.cursor() as cursor:
            cursor.execute("SELECT %s::text[]", (val,))
            return cursor.fetchone()[0]