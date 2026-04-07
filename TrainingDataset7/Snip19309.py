async def test_aincr_version(self):
        """Dummy cache versions can't be incremented."""
        await cache.aset("answer", 42)
        with self.assertRaises(ValueError):
            await cache.aincr_version("answer")
        with self.assertRaises(ValueError):
            await cache.aincr_version("answer", version=2)
        with self.assertRaises(ValueError):
            await cache.aincr_version("does_not_exist")