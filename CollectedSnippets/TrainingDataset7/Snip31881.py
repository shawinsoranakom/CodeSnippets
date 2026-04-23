async def test_keys_async(self):
        await self.session.aset("x", 1)
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(list(await self.session.akeys()), ["x"])
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)