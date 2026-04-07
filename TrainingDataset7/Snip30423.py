def test_mysql_analyze(self):
        qs = Tag.objects.filter(name="test")
        with CaptureQueriesContext(connection) as captured_queries:
            qs.explain(analyze=True)
        self.assertEqual(len(captured_queries), 1)
        prefix = "ANALYZE " if connection.mysql_is_mariadb else "EXPLAIN ANALYZE "
        self.assertTrue(captured_queries[0]["sql"].startswith(prefix))
        with CaptureQueriesContext(connection) as captured_queries:
            qs.explain(analyze=True, format="JSON")
        self.assertEqual(len(captured_queries), 1)
        if connection.mysql_is_mariadb:
            self.assertIn("FORMAT=JSON", captured_queries[0]["sql"])
        else:
            self.assertNotIn("FORMAT=JSON", captured_queries[0]["sql"])