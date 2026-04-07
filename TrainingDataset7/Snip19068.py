def test_delete(self):
        "Cache deletion is transparently ignored on the dummy cache backend"
        cache.set_many({"key1": "spam", "key2": "eggs"})
        self.assertIsNone(cache.get("key1"))
        self.assertIs(cache.delete("key1"), False)
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))