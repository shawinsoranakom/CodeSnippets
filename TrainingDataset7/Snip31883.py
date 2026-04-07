async def test_items_async(self):
        await self.session.aset("x", 1)
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(list(await self.session.aitems()), [("x", 1)])
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)