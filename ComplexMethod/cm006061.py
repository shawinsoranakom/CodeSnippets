async def test_update_project_auth_settings_encryption(
    client: AsyncClient, user_test_project, test_flow_for_update, logged_in_headers
):
    """Test that sensitive auth_settings fields are encrypted when stored."""
    # Create settings with sensitive data
    json_payload = {
        "settings": [
            {
                "id": str(test_flow_for_update.id),
                "action_name": "test_action",
                "action_description": "Test description",
                "mcp_enabled": True,
                "name": test_flow_for_update.name,
                "description": test_flow_for_update.description,
            }
        ],
        "auth_settings": {
            "auth_type": "oauth",
            "oauth_host": "localhost",
            "oauth_port": "3000",
            "oauth_server_url": "http://localhost:3000",
            "oauth_callback_path": "/callback",
            "oauth_client_id": "test-client-id",
            "oauth_client_secret": "test-oauth-secret-value-456",
            "oauth_auth_url": "https://oauth.example.com/auth",
            "oauth_token_url": "https://oauth.example.com/token",
            "oauth_mcp_scope": "read write",
            "oauth_provider_scope": "user:email",
        },
    }

    # Send the update request
    response = await client.patch(
        f"/api/v1/mcp/project/{user_test_project.id}",
        json=json_payload,
        headers=logged_in_headers,
    )
    assert response.status_code == 200

    # Verify the sensitive data is encrypted in the database
    async with session_scope() as session:
        updated_project = await session.get(Folder, user_test_project.id)
        assert updated_project is not None
        assert updated_project.auth_settings is not None

        # Check that sensitive field is encrypted (not plaintext)
        stored_value = updated_project.auth_settings.get("oauth_client_secret")
        assert stored_value is not None
        assert stored_value != "test-oauth-secret-value-456"  # Should be encrypted

        # The encrypted value should be a base64-like string (Fernet token)
        assert len(stored_value) > 50  # Encrypted values are longer

    # Now test that the GET endpoint returns the data (SecretStr will be masked)
    response = await client.get(
        f"/api/v1/mcp/project/{user_test_project.id}",
        headers=logged_in_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # SecretStr fields are masked in the response for security
    assert data["auth_settings"]["oauth_client_secret"] == "**********"  # noqa: S105
    assert data["auth_settings"]["oauth_client_id"] == "test-client-id"
    assert data["auth_settings"]["auth_type"] == "oauth"

    # Verify that decryption is working by checking the actual decrypted value in the backend
    from langflow.services.auth.mcp_encryption import decrypt_auth_settings

    async with session_scope() as session:
        project = await session.get(Folder, user_test_project.id)
        decrypted_settings = decrypt_auth_settings(project.auth_settings)
        assert decrypted_settings["oauth_client_secret"] == "test-oauth-secret-value-456"