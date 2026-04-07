def test_changed_backend_settings(self):
        """
        Removing a backend configured in AUTHENTICATION_BACKENDS makes already
        logged-in users disconnect.
        """
        # Get a session for the test user
        self.assertTrue(
            self.client.login(
                username=self.TEST_USERNAME,
                password=self.TEST_PASSWORD,
            )
        )
        # Prepare a request object
        request = HttpRequest()
        request.session = self.client.session
        # Remove NewModelBackend
        with self.settings(
            AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"]
        ):
            # Get the user from the request
            user = get_user(request)

            # Assert that the user retrieval is successful and the user is
            # anonymous as the backend is not longer available.
            self.assertIsNotNone(user)
            self.assertTrue(user.is_anonymous)