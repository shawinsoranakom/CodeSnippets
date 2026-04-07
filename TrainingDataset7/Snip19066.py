def test_get_many(self):
        "get_many returns nothing for the dummy cache backend"
        cache.set_many({"a": "a", "b": "b", "c": "c", "d": "d"})
        self.assertEqual(cache.get_many(["a", "c", "d"]), {})
        self.assertEqual(cache.get_many(["a", "b", "e"]), {})