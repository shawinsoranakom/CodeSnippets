def test_get_or_set(self):
        self.assertEqual(cache.get_or_set("mykey", "default"), "default")
        self.assertIsNone(cache.get_or_set("mykey", None))