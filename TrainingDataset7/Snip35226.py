def test_with_client(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.client.get(self.url)
        self.assertEqual(len(captured_queries), 1)
        self.assertIn(self.person_pk, captured_queries[0]["sql"])

        with CaptureQueriesContext(connection) as captured_queries:
            self.client.get(self.url)
        self.assertEqual(len(captured_queries), 1)
        self.assertIn(self.person_pk, captured_queries[0]["sql"])

        with CaptureQueriesContext(connection) as captured_queries:
            self.client.get(self.url)
            self.client.get(self.url)
        self.assertEqual(len(captured_queries), 2)
        self.assertIn(self.person_pk, captured_queries[0]["sql"])
        self.assertIn(self.person_pk, captured_queries[1]["sql"])