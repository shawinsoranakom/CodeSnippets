def test_exclude_multivalued_exists(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertSequenceEqual(
                Job.objects.exclude(responsibilities__description="Programming"),
                [self.j1],
            )
        self.assertIn("exists", captured_queries[0]["sql"].lower())