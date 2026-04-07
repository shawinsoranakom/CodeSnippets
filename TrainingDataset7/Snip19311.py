async def test_aget_or_set(self):
        self.assertEqual(await cache.aget_or_set("key", "default"), "default")
        self.assertIsNone(await cache.aget_or_set("key", None))