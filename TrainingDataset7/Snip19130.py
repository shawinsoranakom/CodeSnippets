def test_cache_versioning_delete(self):
        cache.set("answer1", 37, version=1)
        cache.set("answer1", 42, version=2)
        self.assertIs(cache.delete("answer1"), True)
        self.assertIsNone(cache.get("answer1", version=1))
        self.assertEqual(cache.get("answer1", version=2), 42)

        cache.set("answer2", 37, version=1)
        cache.set("answer2", 42, version=2)
        self.assertIs(cache.delete("answer2", version=2), True)
        self.assertEqual(cache.get("answer2", version=1), 37)
        self.assertIsNone(cache.get("answer2", version=2))

        cache.set("answer3", 37, version=1)
        cache.set("answer3", 42, version=2)
        self.assertIs(caches["v2"].delete("answer3"), True)
        self.assertEqual(cache.get("answer3", version=1), 37)
        self.assertIsNone(cache.get("answer3", version=2))

        cache.set("answer4", 37, version=1)
        cache.set("answer4", 42, version=2)
        self.assertIs(caches["v2"].delete("answer4", version=1), True)
        self.assertIsNone(cache.get("answer4", version=1))
        self.assertEqual(cache.get("answer4", version=2), 42)