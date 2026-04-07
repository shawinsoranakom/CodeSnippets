def test_query_default_database_using_model(self):
        query_results = self.run_setup("QueryDefaultDatabaseModelAppConfig")
        self.assertSequenceEqual(query_results, [("new name",)])