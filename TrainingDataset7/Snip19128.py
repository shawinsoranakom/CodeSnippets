def test_cache_versioning_add(self):
        # add, default version = 1, but manually override version = 2
        self.assertIs(cache.add("answer1", 42, version=2), True)
        self.assertIsNone(cache.get("answer1", version=1))
        self.assertEqual(cache.get("answer1", version=2), 42)

        self.assertIs(cache.add("answer1", 37, version=2), False)
        self.assertIsNone(cache.get("answer1", version=1))
        self.assertEqual(cache.get("answer1", version=2), 42)

        self.assertIs(cache.add("answer1", 37, version=1), True)
        self.assertEqual(cache.get("answer1", version=1), 37)
        self.assertEqual(cache.get("answer1", version=2), 42)

        # v2 add, using default version = 2
        self.assertIs(caches["v2"].add("answer2", 42), True)
        self.assertIsNone(cache.get("answer2", version=1))
        self.assertEqual(cache.get("answer2", version=2), 42)

        self.assertIs(caches["v2"].add("answer2", 37), False)
        self.assertIsNone(cache.get("answer2", version=1))
        self.assertEqual(cache.get("answer2", version=2), 42)

        self.assertIs(caches["v2"].add("answer2", 37, version=1), True)
        self.assertEqual(cache.get("answer2", version=1), 37)
        self.assertEqual(cache.get("answer2", version=2), 42)

        # v2 add, default version = 2, but manually override version = 1
        self.assertIs(caches["v2"].add("answer3", 42, version=1), True)
        self.assertEqual(cache.get("answer3", version=1), 42)
        self.assertIsNone(cache.get("answer3", version=2))

        self.assertIs(caches["v2"].add("answer3", 37, version=1), False)
        self.assertEqual(cache.get("answer3", version=1), 42)
        self.assertIsNone(cache.get("answer3", version=2))

        self.assertIs(caches["v2"].add("answer3", 37), True)
        self.assertEqual(cache.get("answer3", version=1), 42)
        self.assertEqual(cache.get("answer3", version=2), 37)