def test_bad_parameter_count(self):
        """
        An executemany call with too many/not enough parameters will raise an
        exception.
        """
        with connection.cursor() as cursor:
            query = "INSERT INTO %s (%s, %s) VALUES (%%s, %%s)" % (
                connection.introspection.identifier_converter("backends_square"),
                connection.ops.quote_name("root"),
                connection.ops.quote_name("square"),
            )
            with self.assertRaises(Exception):
                cursor.executemany(query, [(1, 2, 3)])
            with self.assertRaises(Exception):
                cursor.executemany(query, [(1,)])