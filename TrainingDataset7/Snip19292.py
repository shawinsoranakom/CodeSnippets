async def test_non_existent(self):
        """Nonexistent keys aren't found in the dummy cache backend."""
        self.assertIsNone(await cache.aget("does_not_exist"))
        self.assertEqual(await cache.aget("does_not_exist", "default"), "default")