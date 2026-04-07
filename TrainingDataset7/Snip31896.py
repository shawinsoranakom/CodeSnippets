async def test_save_doesnt_clear_data_async(self):
        await self.session.aset("a", "b")
        await self.session.asave()
        self.assertEqual(await self.session.aget("a"), "b")