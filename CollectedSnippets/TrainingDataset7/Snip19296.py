async def test_ahas_key(self):
        """ahas_key() doesn't ever return True for the dummy cache backend."""
        await cache.aset("hello1", "goodbye1")
        self.assertIs(await cache.ahas_key("hello1"), False)
        self.assertIs(await cache.ahas_key("goodbye1"), False)