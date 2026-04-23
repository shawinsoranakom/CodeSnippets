def test_reverse_encodes_query_string(self):
        self.assertEqual(
            reverse(
                "test",
                query={
                    "hello world": "django project",
                    "foo": [123, 456],
                    "@invalid": ["?", "!", "a b"],
                },
            ),
            "/test/1?hello+world=django+project&foo=123&foo=456"
            "&%40invalid=%3F&%40invalid=%21&%40invalid=a+b",
        )