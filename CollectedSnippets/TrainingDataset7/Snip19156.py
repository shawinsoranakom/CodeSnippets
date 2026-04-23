def test_cull_queries(self):
        old_max_entries = cache._max_entries
        # Force _cull to delete on first cached record.
        cache._max_entries = -1
        with CaptureQueriesContext(connection) as captured_queries:
            try:
                cache.set("force_cull", "value", 1000)
            finally:
                cache._max_entries = old_max_entries
        num_count_queries = sum("COUNT" in query["sql"] for query in captured_queries)
        self.assertEqual(num_count_queries, 1)
        # Column names are quoted.
        for query in captured_queries:
            sql = query["sql"]
            if "expires" in sql:
                self.assertIn(connection.ops.quote_name("expires"), sql)
            if "cache_key" in sql:
                self.assertIn(connection.ops.quote_name("cache_key"), sql)