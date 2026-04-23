def test_login_different_client(self):
        "Using a different test client doesn't violate authentication"

        # Create a second client, and log in.
        c = Client()
        login = c.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")

        # Get a redirection page with the second client.
        response = c.get("/login_protected_redirect_view/")

        # At this points, the self.client isn't logged in.
        # assertRedirects uses the original client, not the default client.
        self.assertRedirects(response, "/get_view/")