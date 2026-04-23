async def test_adecr(self):
        """Dummy cache values can't be decremented."""
        await cache.aset("answer", 42)
        with self.assertRaises(ValueError):
            await cache.adecr("answer")
        with self.assertRaises(ValueError):
            await cache.adecr("does_not_exist")
        with self.assertRaises(ValueError):
            await cache.adecr("does_not_exist", -1)