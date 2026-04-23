def test_query_default_database_using_cursor(self):
        query_results = self.run_setup("QueryDefaultDatabaseCursorAppConfig")
        self.assertSequenceEqual(query_results, [(42,)])