def test_view_with_inactive_force_login(self):
        """
        Request a page that is protected with @login, but use an inactive login
        """

        # Get the page without logging in. Should result in 302.
        response = self.client.get("/login_protected_view/")
        self.assertRedirects(response, "/accounts/login/?next=/login_protected_view/")

        # Log in
        self.client.force_login(
            self.u2, backend="django.contrib.auth.backends.AllowAllUsersModelBackend"
        )

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "inactive")