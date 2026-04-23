def test_success_url_allowed_hosts_unsafe_host(self):
        self.login()
        response = self.client.post("/logout/allowed_hosts/?next=https://evil/")
        self.assertRedirects(
            response, "/logout/allowed_hosts/", fetch_redirect_response=False
        )
        self.confirm_logged_out()