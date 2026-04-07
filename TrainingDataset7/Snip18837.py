def test_cursor_contextmanager_closing(self):
        # There isn't a generic way to test that cursors are closed, but
        # psycopg offers us a way to check that by closed attribute.
        # So, run only on psycopg for that reason.
        with connection.cursor() as cursor:
            self.assertIsInstance(cursor, CursorWrapper)
        self.assertTrue(cursor.closed)