def test_check_password_fake_runtime(self):
        """
        Hasher is run once regardless of whether the user exists. Refs #20760.
        """
        User.objects.create_user("test", "test@example.com", "test")
        User.objects.create_user("inactive", "test@nono.com", "test", is_active=False)
        User.objects.create_user("unusable", "test@nono.com")

        hasher = get_hasher()

        for username, password in [
            ("test", "test"),
            ("test", "wrong"),
            ("inactive", "test"),
            ("inactive", "wrong"),
            ("unusable", "test"),
            ("doesnotexist", "test"),
        ]:
            with (
                self.subTest(username=username, password=password),
                mock.patch.object(hasher, "encode") as mock_make_password,
            ):
                check_password({}, username, password)
                mock_make_password.assert_called_once()