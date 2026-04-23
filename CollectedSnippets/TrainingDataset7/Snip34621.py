def test_view_with_method_force_login(self):
        "Request a page that is protected with a @login_required method"
        # Get the page without logging in. Should result in 302.
        response = self.client.get("/login_protected_method_view/")
        self.assertRedirects(
            response, "/accounts/login/?next=/login_protected_method_view/"
        )

        # Log in
        self.client.force_login(self.u1)

        # Request a page that requires a login
        response = self.client.get("/login_protected_method_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")