def test_success_url_allowed_hosts_safe_host(self):
        response = self.client.post(
            "/login/allowed_hosts/",
            {
                "username": "testclient",
                "password": "password",
                "next": "https://otherserver/home",
            },
        )
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertRedirects(
            response, "https://otherserver/home", fetch_redirect_response=False
        )