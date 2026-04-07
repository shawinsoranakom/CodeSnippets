def test_default_transaction_mode(self):
        with CaptureQueriesContext(connection) as captured_queries:
            with transaction.atomic():
                pass

        begin_query, commit_query = captured_queries
        self.assertEqual(begin_query["sql"], "BEGIN")
        self.assertEqual(commit_query["sql"], "COMMIT")