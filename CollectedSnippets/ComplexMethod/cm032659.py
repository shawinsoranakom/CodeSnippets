def test_user_api_key_removed_from_list_after_deletion(self, admin_session: requests.Session) -> None:
        """Test that deleted API key is removed from the list"""
        user_name: str = EMAIL

        # Generate an API key
        generate_response: dict[str, Any] = generate_user_api_key(admin_session, user_name)
        assert generate_response.get("code") == RetCode.SUCCESS, f"Generate should succeed, got code {generate_response.get('code')}"
        generated_key: dict[str, Any] = generate_response["data"]
        token: str = generated_key["token"]

        # Verify the key exists in the list
        get_response_before: dict[str, Any] = get_user_api_key(admin_session, user_name)
        assert get_response_before.get("code") == RetCode.SUCCESS, f"Get should succeed, got code {get_response_before.get('code')}"
        api_keys_before: list[dict[str, Any]] = get_response_before["data"]
        token_found_before: bool = any(key.get("token") == token for key in api_keys_before)
        assert token_found_before, "Generated API key should be in the list before deletion"

        # Delete the API key
        delete_response: dict[str, Any] = delete_user_api_key(admin_session, user_name, token)
        assert delete_response.get("code") == RetCode.SUCCESS, f"Delete should succeed, got code {delete_response.get('code')}"

        # Verify the key is no longer in the list
        get_response_after: dict[str, Any] = get_user_api_key(admin_session, user_name)
        assert get_response_after.get("code") == RetCode.SUCCESS, f"Get should succeed, got code {get_response_after.get('code')}"
        api_keys_after: list[dict[str, Any]] = get_response_after["data"]
        token_found_after: bool = any(key.get("token") == token for key in api_keys_after)
        assert not token_found_after, "Deleted API key should not be in the list after deletion"