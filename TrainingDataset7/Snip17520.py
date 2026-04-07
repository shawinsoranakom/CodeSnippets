def test_authentication_without_credentials(self):
        CountingMD5PasswordHasher.calls = 0
        for credentials in (
            {},
            {"username": getattr(self.user, self.UserModel.USERNAME_FIELD)},
            {"password": "test"},
        ):
            with self.subTest(credentials=credentials):
                with self.assertNumQueries(0):
                    authenticate(**credentials)
                self.assertEqual(CountingMD5PasswordHasher.calls, 0)