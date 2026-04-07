def test_custom_key_func(self):
        # Two caches with different key functions aren't visible to each other
        cache.set("answer1", 42)
        self.assertEqual(cache.get("answer1"), 42)
        self.assertIsNone(caches["custom_key"].get("answer1"))
        self.assertIsNone(caches["custom_key2"].get("answer1"))

        caches["custom_key"].set("answer2", 42)
        self.assertIsNone(cache.get("answer2"))
        self.assertEqual(caches["custom_key"].get("answer2"), 42)
        self.assertEqual(caches["custom_key2"].get("answer2"), 42)