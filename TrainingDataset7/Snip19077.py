def test_set_many(self):
        "set_many does nothing for the dummy cache backend"
        self.assertEqual(cache.set_many({"a": 1, "b": 2}), [])
        self.assertEqual(cache.set_many({"a": 1, "b": 2}, timeout=2, version="1"), [])