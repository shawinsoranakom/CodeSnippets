async def test_delete_async(self):
        await self.session.asave()
        await self.session.adelete(self.session.session_key)
        self.assertIs(await self.session.aexists(self.session.session_key), False)