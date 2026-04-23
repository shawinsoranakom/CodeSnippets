async def test_get_empty_async(self):
        self.assertIsNone(await self.session.aget("cat"))