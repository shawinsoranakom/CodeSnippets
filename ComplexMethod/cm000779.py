def test_get_login_url_basic(self):
        handler = self._make_handler()
        url = handler.get_login_url(
            scopes=["read", "write"],
            state="random-state-token",
            code_challenge="S256-challenge-value",
        )

        assert "https://auth.example.com/authorize?" in url
        assert "response_type=code" in url
        assert "client_id=test-client-id" in url
        assert "state=random-state-token" in url
        assert "code_challenge=S256-challenge-value" in url
        assert "code_challenge_method=S256" in url
        assert "scope=read+write" in url