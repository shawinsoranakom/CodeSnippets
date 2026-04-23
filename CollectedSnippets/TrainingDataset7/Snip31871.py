async def test_pop_no_default_keyerror_raised_async(self):
        with self.assertRaises(KeyError):
            await self.session.apop("some key")