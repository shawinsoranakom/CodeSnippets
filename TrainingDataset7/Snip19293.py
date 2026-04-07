async def test_aget_many(self):
        """aget_many() returns nothing for the dummy cache backend."""
        await cache.aset_many({"a": "a", "b": "b", "c": "c", "d": "d"})
        self.assertEqual(await cache.aget_many(["a", "c", "d"]), {})
        self.assertEqual(await cache.aget_many(["a", "b", "e"]), {})