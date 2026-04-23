async def test_aadd(self):
        """Add doesn't do anything in dummy cache backend."""
        self.assertIs(await cache.aadd("key", "value"), True)
        self.assertIs(await cache.aadd("key", "new_value"), True)
        self.assertIsNone(await cache.aget("key"))