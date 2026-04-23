def test_simple(self):
        with CaptureQueriesContext(connection) as captured_queries:
            Person.objects.get(pk=self.person_pk)
        self.assertEqual(len(captured_queries), 1)
        self.assertIn(self.person_pk, captured_queries[0]["sql"])

        with CaptureQueriesContext(connection) as captured_queries:
            pass
        self.assertEqual(0, len(captured_queries))