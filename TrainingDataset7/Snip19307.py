async def test_aclear(self):
        """aclear() does nothing for the dummy cache backend."""
        await cache.aclear()