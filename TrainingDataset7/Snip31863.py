async def test_store_async(self):
        await self.session.aset("cat", "dog")
        self.assertIs(self.session.modified, True)
        self.assertEqual(await self.session.apop("cat"), "dog")