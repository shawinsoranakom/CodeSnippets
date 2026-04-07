def test_logout_with_force_login(self):
        "Request a logout after logging in"
        # Log in
        self.client.force_login(self.u1)

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")

        # Log out
        self.client.logout()

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertRedirects(response, "/accounts/login/?next=/login_protected_view/")