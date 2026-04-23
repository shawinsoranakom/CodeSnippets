def test_view_with_inactive_login(self):
        """
        An inactive user may login if the authenticate backend allows it.
        """
        credentials = {"username": "inactive", "password": "password"}
        self.assertFalse(self.client.login(**credentials))

        with self.settings(
            AUTHENTICATION_BACKENDS=[
                "django.contrib.auth.backends.AllowAllUsersModelBackend"
            ]
        ):
            self.assertTrue(self.client.login(**credentials))