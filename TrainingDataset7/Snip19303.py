async def test_aset_many(self):
        """aset_many() does nothing for the dummy cache backend."""
        self.assertEqual(await cache.aset_many({"a": 1, "b": 2}), [])
        self.assertEqual(
            await cache.aset_many({"a": 1, "b": 2}, timeout=2, version="1"),
            [],
        )