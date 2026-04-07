def test_logout_redirect_url_named_setting(self):
        self.login()
        response = self.client.post("/logout/")
        self.assertContains(response, "Logged out")
        self.confirm_logged_out()