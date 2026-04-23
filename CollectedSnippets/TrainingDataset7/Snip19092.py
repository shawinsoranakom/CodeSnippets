def test_get_many(self):
        # Multiple cache keys can be returned using get_many
        cache.set_many({"a": "a", "b": "b", "c": "c", "d": "d"})
        self.assertEqual(
            cache.get_many(["a", "c", "d"]), {"a": "a", "c": "c", "d": "d"}
        )
        self.assertEqual(cache.get_many(["a", "b", "e"]), {"a": "a", "b": "b"})
        self.assertEqual(cache.get_many(iter(["a", "b", "e"])), {"a": "a", "b": "b"})
        cache.set_many({"x": None, "y": 1})
        self.assertEqual(cache.get_many(["x", "y"]), {"x": None, "y": 1})