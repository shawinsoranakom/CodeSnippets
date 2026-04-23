async def test_pop_default_named_argument_async(self):
        self.assertEqual(
            await self.session.apop("some key", default="does not exist"),
            "does not exist",
        )
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)