async def test_pop_default_async(self):
        self.assertEqual(
            await self.session.apop("some key", "does not exist"), "does not exist"
        )
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)