def test_get_or_set(self):
        self.assertIsNone(cache.get("projector"))
        self.assertEqual(cache.get_or_set("projector", 42), 42)
        self.assertEqual(cache.get("projector"), 42)
        self.assertIsNone(cache.get_or_set("null", None))
        # Previous get_or_set() stores None in the cache.
        self.assertIsNone(cache.get("null", "default"))