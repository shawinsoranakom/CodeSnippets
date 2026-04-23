def test_with_client_nested(self):
        with CaptureQueriesContext(connection) as captured_queries:
            Person.objects.count()
            with CaptureQueriesContext(connection):
                pass
            self.client.get(self.url)
        self.assertEqual(2, len(captured_queries))