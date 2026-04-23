async def test_generic_async_acreate(self):
        await self.bacon.tags.acreate(tag="orange")
        self.assertEqual(await self.bacon.tags.acount(), 3)