def test_force_login_with_backend(self):
        """
        Request a page that is protected with @login_required when using
        force_login() and passing a backend.
        """
        # Get the page without logging in. Should result in 302.
        response = self.client.get("/login_protected_view/")
        self.assertRedirects(response, "/accounts/login/?next=/login_protected_view/")

        # Log in
        self.client.force_login(
            self.u1, backend="test_client.auth_backends.TestClientBackend"
        )
        self.assertEqual(self.u1.backend, "test_client.auth_backends.TestClientBackend")

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")