def test_delete(self):
        # Cache keys can be deleted
        cache.set_many({"key1": "spam", "key2": "eggs"})
        self.assertEqual(cache.get("key1"), "spam")
        self.assertIs(cache.delete("key1"), True)
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "eggs")