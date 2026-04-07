async def test_aclose(self):
        """aclose() does nothing for the dummy cache backend."""
        await cache.aclose()