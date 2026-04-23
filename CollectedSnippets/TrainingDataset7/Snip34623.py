def test_view_with_force_login_and_custom_redirect(self):
        """
        Request a page that is protected with
        @login_required(redirect_field_name='redirect_to')
        """
        # Get the page without logging in. Should result in 302.
        response = self.client.get("/login_protected_view_custom_redirect/")
        self.assertRedirects(
            response,
            "/accounts/login/?redirect_to=/login_protected_view_custom_redirect/",
        )

        # Log in
        self.client.force_login(self.u1)

        # Request a page that requires a login
        response = self.client.get("/login_protected_view_custom_redirect/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")