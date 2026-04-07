async def test_expiration(self):
        """Expiration has no effect on the dummy cache."""
        await cache.aset("expire1", "very quickly", 1)
        await cache.aset("expire2", "very quickly", 1)
        await cache.aset("expire3", "very quickly", 1)

        await asyncio.sleep(2)
        self.assertIsNone(await cache.aget("expire1"))

        self.assertIs(await cache.aadd("expire2", "new_value"), True)
        self.assertIsNone(await cache.aget("expire2"))
        self.assertIs(await cache.ahas_key("expire3"), False)