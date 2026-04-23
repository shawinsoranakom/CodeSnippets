def test_cursor_var(self):
        """Cursor variables can be passed as query parameters."""
        with connection.cursor() as cursor:
            var = cursor.var(str)
            cursor.execute("BEGIN %s := 'X'; END; ", [var])
            self.assertEqual(var.getvalue(), "X")