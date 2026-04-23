def test_logout_redirect_url_setting_allowed_hosts_unsafe_host(self):
        self.login()
        response = self.client.post("/logout/allowed_hosts/?next=https://evil/")
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)