def test_query_other_database_using_model(self):
        query_results = self.run_setup("QueryOtherDatabaseModelAppConfig")
        self.assertSequenceEqual(query_results, [("new name",)])