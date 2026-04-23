def test_mysql_text_to_traditional(self):
        # Ensure these cached properties are initialized to prevent queries for
        # the MariaDB or MySQL version during the QuerySet evaluation.
        connection.features.supported_explain_formats
        with CaptureQueriesContext(connection) as captured_queries:
            Tag.objects.filter(name="test").explain(format="text")
        self.assertEqual(len(captured_queries), 1)
        self.assertIn("FORMAT=TRADITIONAL", captured_queries[0]["sql"])