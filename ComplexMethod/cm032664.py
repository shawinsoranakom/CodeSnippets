def test_generate_user_api_key_timestamp_fields(self, admin_session: requests.Session) -> None:
        """Test that generated API key has correct timestamp fields"""
        user_name: str = EMAIL

        response: Dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert response.get("code") == RetCode.SUCCESS, f"Response code should be {RetCode.SUCCESS}, got {response.get('code')}"
        result: Dict[str, Any] = response["data"]

        # create_time should be a timestamp (int)
        create_time: Any = result.get("create_time")
        assert create_time is None or isinstance(create_time, int), "create_time should be int or None"
        if create_time is not None:
            assert create_time > 0, "create_time should be positive"

        # create_date should be a date string
        create_date: Any = result.get("create_date")
        assert create_date is None or isinstance(create_date, str), "create_date should be string or None"

        # update_time and update_date should be None for new keys
        assert result.get("update_time") is None, "update_time should be None for new keys"
        assert result.get("update_date") is None, "update_date should be None for new keys"