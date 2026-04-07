def test_success_url_allowed_hosts_same_host(self):
        self.login()
        response = self.client.post("/logout/allowed_hosts/?next=https://testserver/")
        self.assertRedirects(
            response, "https://testserver/", fetch_redirect_response=False
        )
        self.confirm_logged_out()