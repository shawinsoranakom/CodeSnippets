def test_queries(self):
        """
        Test the documented API of connection.queries.
        """
        sql = "SELECT 1" + connection.features.bare_select_suffix
        with connection.cursor() as cursor:
            reset_queries()
            cursor.execute(sql)
        self.assertEqual(1, len(connection.queries))
        self.assertIsInstance(connection.queries, list)
        self.assertIsInstance(connection.queries[0], dict)
        self.assertEqual(list(connection.queries[0]), ["sql", "time"])
        self.assertEqual(connection.queries[0]["sql"], sql)

        reset_queries()
        self.assertEqual(0, len(connection.queries))

        sql = "INSERT INTO %s (%s, %s) VALUES (%%s, %%s)" % (
            connection.introspection.identifier_converter("backends_square"),
            connection.ops.quote_name("root"),
            connection.ops.quote_name("square"),
        )
        with connection.cursor() as cursor:
            cursor.executemany(sql, [(1, 1), (2, 4)])
        self.assertEqual(1, len(connection.queries))
        self.assertIsInstance(connection.queries, list)
        self.assertIsInstance(connection.queries[0], dict)
        self.assertEqual(list(connection.queries[0]), ["sql", "time"])
        self.assertEqual(connection.queries[0]["sql"], "2 times: %s" % sql)