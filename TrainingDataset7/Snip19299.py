async def test_atouch(self):
        self.assertIs(await cache.atouch("key"), False)