async def test_aremove(self):
        await self.bacon.tags.aremove(self.fatty)
        self.assertEqual(await self.bacon.tags.acount(), 1)
        await self.bacon.tags.aremove(self.salty)
        self.assertEqual(await self.bacon.tags.acount(), 0)