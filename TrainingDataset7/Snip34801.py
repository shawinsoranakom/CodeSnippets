def test_logout(self):
        """Logout should work whether the user is logged in or not (#9978)."""
        self.client.logout()
        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")
        self.client.logout()
        self.client.logout()