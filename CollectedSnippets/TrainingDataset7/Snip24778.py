def test_immutable_get_with_default(self):
        q = QueryDict()
        self.assertEqual(q.get("foo", "default"), "default")