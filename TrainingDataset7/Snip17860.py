def test_check_password_custom_user(self):
        """
        check_password() returns the correct values as per
        https://modwsgi.readthedocs.io/en/develop/user-guides/access-control-mechanisms.html#apache-authentication-provider
        with a custom user installed.
        """
        CustomUser._default_manager.create_user(
            "test@example.com", "1990-01-01", "test"
        )

        # User not in database
        self.assertIsNone(check_password({}, "unknown", ""))

        # Valid user with correct password'
        self.assertIs(check_password({}, "test@example.com", "test"), True)

        # Valid user with incorrect password
        self.assertIs(check_password({}, "test@example.com", "incorrect"), False)