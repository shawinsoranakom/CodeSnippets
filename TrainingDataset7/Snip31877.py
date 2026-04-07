async def test_has_key_async(self):
        await self.session.aset("some key", 1)
        self.session.modified = False
        self.session.accessed = False
        self.assertIs(await self.session.ahas_key("some key"), True)
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)