async def test_adecr_version(self):
        """Dummy cache versions can't be decremented."""
        await cache.aset("answer", 42)
        with self.assertRaises(ValueError):
            await cache.adecr_version("answer")
        with self.assertRaises(ValueError):
            await cache.adecr_version("answer", version=2)
        with self.assertRaises(ValueError):
            await cache.adecr_version("does_not_exist")