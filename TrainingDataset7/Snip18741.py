def test_no_interpolation(self):
        # This shouldn't raise an exception (#17158)
        query = "SELECT strftime('%Y', 'now');"
        with connection.cursor() as cursor:
            cursor.execute(query)
        self.assertEqual(connection.queries[-1]["sql"], query)