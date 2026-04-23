def test_logout_with_post(self):
        self.login()
        response = self.client.post("/logout/")
        self.assertContains(response, "Logged out")
        self.confirm_logged_out()