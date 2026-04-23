def test_has_stats(self):
        self.mock_stats = [
            CacheStat(
                category_name="st.singleton",
                cache_name="foo",
                byte_length=128,
            ),
            CacheStat(
                category_name="st.memo",
                cache_name="bar",
                byte_length=256,
            ),
        ]

        response = self.fetch("/st-metrics")
        self.assertEqual(200, response.code)
        self.assertEqual(
            "application/openmetrics-text", response.headers.get("Content-Type")
        )

        expected_body = (
            "# TYPE cache_memory_bytes gauge\n"
            "# UNIT cache_memory_bytes bytes\n"
            "# HELP Total memory consumed by a cache.\n"
            'cache_memory_bytes{cache_type="st.singleton",cache="foo"} 128\n'
            'cache_memory_bytes{cache_type="st.memo",cache="bar"} 256\n'
            "# EOF\n"
        ).encode("utf-8")

        self.assertEqual(expected_body, response.body)