def test_get_or_set_version(self):
        msg = "get_or_set() missing 1 required positional argument: 'default'"
        self.assertEqual(cache.get_or_set("brian", 1979, version=2), 1979)
        with self.assertRaisesMessage(TypeError, msg):
            cache.get_or_set("brian")
        with self.assertRaisesMessage(TypeError, msg):
            cache.get_or_set("brian", version=1)
        self.assertIsNone(cache.get("brian", version=1))
        self.assertEqual(cache.get_or_set("brian", 42, version=1), 42)
        self.assertEqual(cache.get_or_set("brian", 1979, version=2), 1979)
        self.assertIsNone(cache.get("brian", version=3))