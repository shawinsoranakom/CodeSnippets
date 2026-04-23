def test_get_user_api_key_tenant_id_consistency(self, admin_session: requests.Session) -> None:
        """Test that all API keys for a user have the same tenant_id"""
        user_name: str = EMAIL

        # Generate multiple API keys
        response1: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response1["code"] == RetCode.SUCCESS, response1
        response2: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response2["code"] == RetCode.SUCCESS, response2

        # Get all API keys
        get_response: Dict[str, Any] = get_user_api_key(admin_session, user_name)
        assert get_response["code"] == RetCode.SUCCESS, get_response
        api_keys: List[Dict[str, Any]] = get_response["data"]

        # Verify all keys have the same tenant_id
        tenant_ids: List[str] = [key.get("tenant_id") for key in api_keys if key.get("tenant_id")]
        if len(tenant_ids) > 0:
            assert all(tid == tenant_ids[0] for tid in tenant_ids), "All API keys should have the same tenant_id"