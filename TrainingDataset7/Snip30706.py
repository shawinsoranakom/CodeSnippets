def test_sliced_distinct_exists(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertIs(Article.objects.distinct()[1:3].exists(), False)
        self.assertEqual(len(captured_queries), 1)
        captured_sql = captured_queries[0]["sql"]
        self.assertIn(connection.ops.quote_name("id"), captured_sql)
        self.assertIn(connection.ops.quote_name("name"), captured_sql)