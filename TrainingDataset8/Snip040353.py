def test_no_stats(self):
        """If we have no stats, we expect to see just the header and footer."""
        response = self.fetch("/st-metrics")
        self.assertEqual(200, response.code)

        expected_body = (
            "# TYPE cache_memory_bytes gauge\n"
            "# UNIT cache_memory_bytes bytes\n"
            "# HELP Total memory consumed by a cache.\n"
            "# EOF\n"
        ).encode("utf-8")

        self.assertEqual(expected_body, response.body)