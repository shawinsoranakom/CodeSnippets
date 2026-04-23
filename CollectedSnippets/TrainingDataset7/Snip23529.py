async def test_aclear(self):
        await self.bacon.tags.aclear()
        self.assertEqual(await self.bacon.tags.acount(), 0)