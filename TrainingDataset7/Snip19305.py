async def test_adelete_many(self):
        """adelete_many() does nothing for the dummy cache backend."""
        await cache.adelete_many(["a", "b"])