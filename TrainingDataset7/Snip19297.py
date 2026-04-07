async def test_aincr(self):
        """Dummy cache values can't be incremented."""
        await cache.aset("answer", 42)
        with self.assertRaises(ValueError):
            await cache.aincr("answer")
        with self.assertRaises(ValueError):
            await cache.aincr("does_not_exist")
        with self.assertRaises(ValueError):
            await cache.aincr("does_not_exist", -1)