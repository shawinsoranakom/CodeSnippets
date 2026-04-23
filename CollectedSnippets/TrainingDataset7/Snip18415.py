def test_logout_redirect_url_setting(self):
        self.login()
        response = self.client.post("/logout/")
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)