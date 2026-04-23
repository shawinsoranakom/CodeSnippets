def test_multiple_caches(self):
        "Multiple locmem caches are isolated"
        cache.set("value", 42)
        self.assertEqual(caches["default"].get("value"), 42)
        self.assertIsNone(caches["other"].get("value"))