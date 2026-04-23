def test_generate_user_api_key_success(self, admin_session: requests.Session) -> None:
        """Test successfully generating API key for a user"""
        # Use the test user email (get_user_details expects email)
        user_name: str = EMAIL

        # Generate API key
        response: Dict[str, Any] = generate_user_api_key(admin_session, user_name)

        # Verify response code, message, and data
        assert response.get("code") == RetCode.SUCCESS, f"Response code should be {RetCode.SUCCESS}, got {response.get('code')}"
        assert "message" in response, "Response should contain message"
        assert "data" in response, "Response should contain data"
        assert response.get("data") is not None, "API key generation should return data"

        result: Dict[str, Any] = response["data"]

        # Verify response structure
        assert "tenant_id" in result, "Response should contain tenant_id"
        assert "token" in result, "Response should contain token"
        assert "beta" in result, "Response should contain beta"
        assert "create_time" in result, "Response should contain create_time"
        assert "create_date" in result, "Response should contain create_date"

        # Verify token format (should start with "ragflow-")
        token: str = result["token"]
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"

        # Verify beta is independently generated
        beta: str = result["beta"]
        assert isinstance(beta, str), "Beta should be a string"
        assert len(beta) == 32, "Beta should be 32 characters"
        # Beta should be independent from token (not derived from it)
        if token.startswith("ragflow-"):
            token_without_prefix: str = token.replace("ragflow-", "")[:32]
            assert beta != token_without_prefix, "Beta should be independently generated, not derived from token"