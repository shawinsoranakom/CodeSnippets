def test_cache_versioning_get_set(self):
        # set, using default version = 1
        cache.set("answer1", 42)
        self.assertEqual(cache.get("answer1"), 42)
        self.assertEqual(cache.get("answer1", version=1), 42)
        self.assertIsNone(cache.get("answer1", version=2))

        self.assertIsNone(caches["v2"].get("answer1"))
        self.assertEqual(caches["v2"].get("answer1", version=1), 42)
        self.assertIsNone(caches["v2"].get("answer1", version=2))

        # set, default version = 1, but manually override version = 2
        cache.set("answer2", 42, version=2)
        self.assertIsNone(cache.get("answer2"))
        self.assertIsNone(cache.get("answer2", version=1))
        self.assertEqual(cache.get("answer2", version=2), 42)

        self.assertEqual(caches["v2"].get("answer2"), 42)
        self.assertIsNone(caches["v2"].get("answer2", version=1))
        self.assertEqual(caches["v2"].get("answer2", version=2), 42)

        # v2 set, using default version = 2
        caches["v2"].set("answer3", 42)
        self.assertIsNone(cache.get("answer3"))
        self.assertIsNone(cache.get("answer3", version=1))
        self.assertEqual(cache.get("answer3", version=2), 42)

        self.assertEqual(caches["v2"].get("answer3"), 42)
        self.assertIsNone(caches["v2"].get("answer3", version=1))
        self.assertEqual(caches["v2"].get("answer3", version=2), 42)

        # v2 set, default version = 2, but manually override version = 1
        caches["v2"].set("answer4", 42, version=1)
        self.assertEqual(cache.get("answer4"), 42)
        self.assertEqual(cache.get("answer4", version=1), 42)
        self.assertIsNone(cache.get("answer4", version=2))

        self.assertIsNone(caches["v2"].get("answer4"))
        self.assertEqual(caches["v2"].get("answer4", version=1), 42)
        self.assertIsNone(caches["v2"].get("answer4", version=2))