def is_usable(self):
        if self.connection is None:
            return False
        try:
            # Use a psycopg cursor directly, bypassing Django's utilities.
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Database.Error:
            return False
        else:
            return True