def test_reverse_with_query(self):
        self.assertEqual(
            reverse("test", query={"hello": "world", "foo": 123}),
            "/test/1?hello=world&foo=123",
        )