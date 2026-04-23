def test_incr_version(self):
        cache.set("answer", 42, version=2)
        self.assertIsNone(cache.get("answer"))
        self.assertIsNone(cache.get("answer", version=1))
        self.assertEqual(cache.get("answer", version=2), 42)
        self.assertIsNone(cache.get("answer", version=3))

        self.assertEqual(cache.incr_version("answer", version=2), 3)
        self.assertIsNone(cache.get("answer"))
        self.assertIsNone(cache.get("answer", version=1))
        self.assertIsNone(cache.get("answer", version=2))
        self.assertEqual(cache.get("answer", version=3), 42)

        caches["v2"].set("answer2", 42)
        self.assertEqual(caches["v2"].get("answer2"), 42)
        self.assertIsNone(caches["v2"].get("answer2", version=1))
        self.assertEqual(caches["v2"].get("answer2", version=2), 42)
        self.assertIsNone(caches["v2"].get("answer2", version=3))

        self.assertEqual(caches["v2"].incr_version("answer2"), 3)
        self.assertIsNone(caches["v2"].get("answer2"))
        self.assertIsNone(caches["v2"].get("answer2", version=1))
        self.assertIsNone(caches["v2"].get("answer2", version=2))
        self.assertEqual(caches["v2"].get("answer2", version=3), 42)

        with self.assertRaises(ValueError):
            cache.incr_version("does_not_exist")

        cache.set("null", None)
        self.assertEqual(cache.incr_version("null"), 2)