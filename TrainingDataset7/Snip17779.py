def test_get_invalid_login_error(self):
        error = AuthenticationForm().get_invalid_login_error()
        self.assertIsInstance(error, ValidationError)
        self.assertEqual(
            error.message,
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive.",
        )
        self.assertEqual(error.code, "invalid_login")
        self.assertEqual(error.params, {"username": "username"})