def test_logout_default(self):
        "Logout without next_page option renders the default template"
        self.login()
        response = self.client.post("/logout/")
        self.assertContains(response, "Logged out")
        self.confirm_logged_out()