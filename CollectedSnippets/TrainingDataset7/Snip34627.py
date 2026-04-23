def test_logout(self):
        "Request a logout after logging in"
        # Log in
        self.client.login(username="testclient", password="password")

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")

        # Log out
        self.client.logout()

        # Request a page that requires a login
        response = self.client.get("/login_protected_view/")
        self.assertRedirects(response, "/accounts/login/?next=/login_protected_view/")