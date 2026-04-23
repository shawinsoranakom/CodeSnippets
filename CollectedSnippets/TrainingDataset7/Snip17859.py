def test_check_password(self):
        """
        check_password() returns the correct values as per
        https://modwsgi.readthedocs.io/en/develop/user-guides/access-control-mechanisms.html#apache-authentication-provider
        """
        User.objects.create_user("test", "test@example.com", "test")

        # User not in database
        self.assertIsNone(check_password({}, "unknown", ""))

        # Valid user with correct password
        self.assertIs(check_password({}, "test", "test"), True)

        # Valid user with incorrect password
        self.assertIs(check_password({}, "test", "incorrect"), False)

        # correct password, but user is inactive
        User.objects.filter(username="test").update(is_active=False)
        self.assertIsNone(check_password({}, "test", "test"))