async def test_save_async(self):
        await self.session.asave()
        self.assertIs(await self.session.aexists(self.session.session_key), True)