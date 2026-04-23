def test_get_user_api_key_success(self, admin_session: requests.Session) -> None:
        """Test successfully getting API keys for a user with correct response structure"""
        user_name: str = EMAIL

        # Generate a test API key first
        generate_response: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert generate_response["code"] == RetCode.SUCCESS, generate_response
        generated_key: Dict[str, Any] = generate_response["data"]
        generated_token: str = generated_key["token"]

        # Get all API keys for the user
        get_response: Dict[str, Any] = get_user_api_key(admin_session, user_name)
        assert get_response["code"] == RetCode.SUCCESS, get_response
        assert "message" in get_response, "Response should contain message"
        assert "data" in get_response, "Response should contain data"

        api_keys: List[Dict[str, Any]] = get_response["data"]

        # Verify response is a list with at least one key
        assert isinstance(api_keys, list), "API keys should be returned as a list"
        assert len(api_keys) > 0, "User should have at least one API key"

        # Verify structure of each API key
        for key in api_keys:
            assert isinstance(key, dict), "Each API key should be a dictionary"
            assert "token" in key, "API key should contain token"
            assert "beta" in key, "API key should contain beta"
            assert "tenant_id" in key, "API key should contain tenant_id"
            assert "create_date" in key, "API key should contain create_date"

            # Verify field types
            assert isinstance(key["token"], str), "token should be string"
            assert isinstance(key["beta"], str), "beta should be string"
            assert isinstance(key["tenant_id"], str), "tenant_id should be string"
            assert isinstance(key.get("create_date"), (str, type(None))), "create_date should be string or None"
            assert isinstance(key.get("update_date"), (str, type(None))), "update_date should be string or None"

        # Verify the generated key is in the list
        token_found: bool = any(key.get("token") == generated_token for key in api_keys)
        assert token_found, "Generated API key should appear in the list"