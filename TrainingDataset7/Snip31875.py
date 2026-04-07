async def test_update_async(self):
        await self.session.aupdate({"update key": 1})
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, True)
        self.assertEqual(await self.session.aget("update key", None), 1)