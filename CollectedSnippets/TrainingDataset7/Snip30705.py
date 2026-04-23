def test_distinct_exists(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertIs(Article.objects.distinct().exists(), False)
        self.assertEqual(len(captured_queries), 1)
        captured_sql = captured_queries[0]["sql"]
        self.assertNotIn(connection.ops.quote_name("id"), captured_sql)
        self.assertNotIn(connection.ops.quote_name("name"), captured_sql)