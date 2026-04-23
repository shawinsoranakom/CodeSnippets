async def test_values_async(self):
        self.assertEqual(list(await self.session.avalues()), [])
        self.assertIs(self.session.accessed, True)
        await self.session.aset("some key", 1)
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(list(await self.session.avalues()), [1])
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)