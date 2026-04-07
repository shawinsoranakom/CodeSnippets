def test_reverse_with_query_and_fragment(self):
        self.assertEqual(
            reverse("test", query={"hello": "world", "foo": 123}, fragment="tab-1"),
            "/test/1?hello=world&foo=123#tab-1",
        )