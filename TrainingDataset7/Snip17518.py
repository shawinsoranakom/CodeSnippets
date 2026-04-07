def test_authentication_timing(self):
        """
        Hasher is run once regardless of whether the user exists. Refs #20760.
        """
        # Re-set the password, because this tests overrides PASSWORD_HASHERS
        self.user.set_password("test")
        self.user.save()

        CountingMD5PasswordHasher.calls = 0
        username = getattr(self.user, self.UserModel.USERNAME_FIELD)
        authenticate(username=username, password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

        CountingMD5PasswordHasher.calls = 0
        authenticate(username="no_such_user", password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)