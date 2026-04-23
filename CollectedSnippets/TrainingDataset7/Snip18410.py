def test_success_url_allowed_hosts_safe_host(self):
        self.login()
        response = self.client.post("/logout/allowed_hosts/?next=https://otherserver/")
        self.assertRedirects(
            response, "https://otherserver/", fetch_redirect_response=False
        )
        self.confirm_logged_out()