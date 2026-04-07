def test_query_other_database_using_cursor(self):
        query_results = self.run_setup("QueryOtherDatabaseCursorAppConfig")
        self.assertSequenceEqual(query_results, [(42,)])