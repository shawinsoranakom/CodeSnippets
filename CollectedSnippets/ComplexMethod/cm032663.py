def test_generate_user_api_key_token_format(self, admin_session: requests.Session) -> None:
        """Test that generated API key has correct format"""
        user_name: str = EMAIL

        response: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response.get("code") == RetCode.SUCCESS, f"Response code should be {RetCode.SUCCESS}, got {response.get('code')}"
        result: Dict[str, Any] = response["data"]
        token: str = result["token"]

        # Token should be a non-empty string
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"

        # Beta should be independently generated (32 chars, not derived from token)
        beta: str = result["beta"]
        assert isinstance(beta, str), "Beta should be a string"
        assert len(beta) == 32, "Beta should be 32 characters"
        # Beta should be independent from token (not derived from it)
        if token.startswith("ragflow-"):
            token_without_prefix: str = token.replace("ragflow-", "")[:32]
            assert beta != token_without_prefix, "Beta should be independently generated, not derived from token"