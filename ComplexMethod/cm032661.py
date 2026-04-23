def test_generate_user_api_key_response_structure(self, admin_session: requests.Session) -> None:
        """Test that generate_user_api_key returns correct response structure"""
        user_name: str = EMAIL

        response: Dict[str, Any] = generate_user_api_key(admin_session, user_name)

        # Verify response code, message, and data
        assert response.get("code") == RetCode.SUCCESS, f"Response code should be {RetCode.SUCCESS}, got {response.get('code')}"
        assert "message" in response, "Response should contain message"
        assert "data" in response, "Response should contain data"

        result: Dict[str, Any] = response["data"]

        # Verify all required fields
        assert "tenant_id" in result, "Response should have tenant_id"
        assert "token" in result, "Response should have token"
        assert "beta" in result, "Response should have beta"
        assert "create_time" in result, "Response should have create_time"
        assert "create_date" in result, "Response should have create_date"
        assert "update_time" in result, "Response should have update_time"
        assert "update_date" in result, "Response should have update_date"

        # Verify field types
        assert isinstance(result["tenant_id"], str), "tenant_id should be string"
        assert isinstance(result["token"], str), "token should be string"
        assert isinstance(result["beta"], str), "beta should be string"
        assert isinstance(result["create_time"], (int, type(None))), "create_time should be int or None"
        assert isinstance(result["create_date"], (str, type(None))), "create_date should be string or None"