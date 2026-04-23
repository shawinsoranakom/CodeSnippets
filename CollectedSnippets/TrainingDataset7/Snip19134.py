def test_decr_version(self):
        cache.set("answer", 42, version=2)
        self.assertIsNone(cache.get("answer"))
        self.assertIsNone(cache.get("answer", version=1))
        self.assertEqual(cache.get("answer", version=2), 42)

        self.assertEqual(cache.decr_version("answer", version=2), 1)
        self.assertEqual(cache.get("answer"), 42)
        self.assertEqual(cache.get("answer", version=1), 42)
        self.assertIsNone(cache.get("answer", version=2))

        caches["v2"].set("answer2", 42)
        self.assertEqual(caches["v2"].get("answer2"), 42)
        self.assertIsNone(caches["v2"].get("answer2", version=1))
        self.assertEqual(caches["v2"].get("answer2", version=2), 42)

        self.assertEqual(caches["v2"].decr_version("answer2"), 1)
        self.assertIsNone(caches["v2"].get("answer2"))
        self.assertEqual(caches["v2"].get("answer2", version=1), 42)
        self.assertIsNone(caches["v2"].get("answer2", version=2))

        with self.assertRaises(ValueError):
            cache.decr_version("does_not_exist", version=2)

        cache.set("null", None, version=2)
        self.assertEqual(cache.decr_version("null", version=2), 1)