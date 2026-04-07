def test_success_url_allowed_hosts_unsafe_host(self):
        response = self.client.post(
            "/login/allowed_hosts/",
            {
                "username": "testclient",
                "password": "password",
                "next": "https://evil/home",
            },
        )
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertRedirects(
            response, "/accounts/profile/", fetch_redirect_response=False
        )