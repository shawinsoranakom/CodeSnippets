def test_login(self):
        "A session engine that modifies the session key can be used to log in"
        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")

        # Try to access a login protected page.
        response = self.client.get("/login_protected_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")