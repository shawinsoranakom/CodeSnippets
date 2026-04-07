async def test_pop_async(self):
        await self.session.aset("some key", "exists")
        # Need to reset these to pretend we haven't accessed it:
        self.accessed = False
        self.modified = False

        self.assertEqual(await self.session.apop("some key"), "exists")
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, True)
        self.assertIsNone(await self.session.aget("some key"))