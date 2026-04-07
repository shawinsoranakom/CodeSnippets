def test_has_key_query_columns_quoted(self):
        with CaptureQueriesContext(connection) as captured_queries:
            cache.has_key("key")
        self.assertEqual(len(captured_queries), 1)
        sql = captured_queries[0]["sql"]
        # Column names are quoted.
        self.assertIn(connection.ops.quote_name("expires"), sql)
        self.assertIn(connection.ops.quote_name("cache_key"), sql)