def test_reverse_with_query_sequences(self):
        cases = [
            [("hello", "world"), ("foo", 123), ("foo", 456)],
            (("hello", "world"), ("foo", 123), ("foo", 456)),
            {"hello": "world", "foo": (123, 456)},
        ]
        for query in cases:
            with self.subTest(query=query):
                self.assertEqual(
                    reverse("test", query=query), "/test/1?hello=world&foo=123&foo=456"
                )