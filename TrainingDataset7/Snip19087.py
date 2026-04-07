def test_simple(self):
        # Simple cache set/get works
        cache.set("key", "value")
        self.assertEqual(cache.get("key"), "value")