def test_generate_user_api_key_multiple_times(self, admin_session: requests.Session) -> None:
        """Test generating multiple API keys for the same user"""
        user_name: str = EMAIL

        # Generate first API key
        response1: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response1.get("code") == RetCode.SUCCESS, f"First generate should succeed, got code {response1.get('code')}"
        key1: Dict[str, Any] = response1["data"]
        token1: str = key1["token"]

        # Generate second API key
        response2: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response2.get("code") == RetCode.SUCCESS, f"Second generate should succeed, got code {response2.get('code')}"
        key2: Dict[str, Any] = response2["data"]
        token2: str = key2["token"]

        # Tokens should be different
        assert token1 != token2, "Multiple API keys should have different tokens"

        # Both should appear in the list
        get_response: Dict[str, Any] = get_user_api_key(admin_session, user_name)
        assert get_response.get("code") == RetCode.SUCCESS, f"Get should succeed, got code {get_response.get('code')}"
        api_keys: List[Dict[str, Any]] = get_response["data"]
        tokens: List[str] = [key.get("token") for key in api_keys]
        assert token1 in tokens, "First token should be in the list"
        assert token2 in tokens, "Second token should be in the list"