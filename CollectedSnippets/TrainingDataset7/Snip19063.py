def test_simple(self):
        "Dummy cache backend ignores cache set calls"
        cache.set("key", "value")
        self.assertIsNone(cache.get("key"))