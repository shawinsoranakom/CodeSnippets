def test_success_url_allowed_hosts_same_host(self):
        response = self.client.post(
            "/login/allowed_hosts/",
            {
                "username": "testclient",
                "password": "password",
                "next": "https://testserver/home",
            },
        )
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertRedirects(
            response, "https://testserver/home", fetch_redirect_response=False
        )