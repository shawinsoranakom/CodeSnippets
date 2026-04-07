async def test_aauthenticate_inactive(self):
        """
        An inactive user can't authenticate.
        """
        self.assertEqual(await aauthenticate(**self.user_credentials), self.user)
        self.user.is_active = False
        await self.user.asave()
        self.assertIsNone(await aauthenticate(**self.user_credentials))