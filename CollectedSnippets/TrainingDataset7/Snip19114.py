def test_clear(self):
        # The cache can be emptied using clear
        cache.set_many({"key1": "spam", "key2": "eggs"})
        cache.clear()
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))