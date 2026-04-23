async def test_flush_async(self):
        await self.session.aset("foo", "bar")
        await self.session.asave()
        prev_key = self.session.session_key
        await self.session.aflush()
        self.assertIs(await self.session.aexists(prev_key), False)
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertIsNone(self.session.session_key)
        self.assertIs(self.session.modified, True)
        self.assertIs(self.session.accessed, True)