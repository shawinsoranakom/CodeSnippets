async def test_aauthentication_timing(self):
        """See test_authentication_timing()"""
        # Re-set the password, because this tests overrides PASSWORD_HASHERS.
        self.user.set_password("test")
        await self.user.asave()

        CountingMD5PasswordHasher.calls = 0
        username = getattr(self.user, self.UserModel.USERNAME_FIELD)
        await aauthenticate(username=username, password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

        CountingMD5PasswordHasher.calls = 0
        await aauthenticate(username="no_such_user", password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)