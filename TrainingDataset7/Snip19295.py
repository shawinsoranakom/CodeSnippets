async def test_adelete(self):
        """
        Cache deletion is transparently ignored on the dummy cache backend.
        """
        await cache.aset_many({"key1": "spam", "key2": "eggs"})
        self.assertIsNone(await cache.aget("key1"))
        self.assertIs(await cache.adelete("key1"), False)
        self.assertIsNone(await cache.aget("key1"))
        self.assertIsNone(await cache.aget("key2"))