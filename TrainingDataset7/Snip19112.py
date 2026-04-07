def test_delete_many(self):
        # Multiple keys can be deleted using delete_many
        cache.set_many({"key1": "spam", "key2": "eggs", "key3": "ham"})
        cache.delete_many(["key1", "key2"])
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key3"), "ham")