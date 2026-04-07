async def test_simple(self):
        """Dummy cache backend ignores cache set calls."""
        await cache.aset("key", "value")
        self.assertIsNone(await cache.aget("key"))