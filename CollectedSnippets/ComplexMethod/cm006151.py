async def test_cross_user_mcp_server_access_prevention(
        self,
        client: AsyncClient,
        user_one_api_key: str,
        user_two_api_key: str,
        transport,
    ):
        """Verify that users cannot access or modify each other's MCP servers,even if they have the same name."""
        server_name = f"shared-server-name-{uuid4()}"
        if transport == "streamable":
            config_one = {
                "command": "uvx",
                "args": ["mcp-proxy", "--transport", "streamablehttp", f"url-one-{uuid4()}"],
            }
            config_two = {
                "command": "uvx",
                "args": ["mcp-proxy", "--transport", "streamablehttp", f"url-two-{uuid4()}"],
            }
            updated_config_one = {
                "command": "uvx",
                "args": ["mcp-proxy", "--transport", "streamablehttp", f"updated-url-one-{uuid4()}"],
            }
        else:
            config_one = {"command": "uvx", "args": ["mcp-proxy", f"url-one-{uuid4()}"]}
            config_two = {"command": "uvx", "args": ["mcp-proxy", f"url-two-{uuid4()}"]}
            updated_config_one = {"command": "uvx", "args": ["mcp-proxy", f"updated-url-one-{uuid4()}"]}

        # User One creates a server
        response = await client.post(
            f"/api/v2/mcp/servers/{server_name}",
            json=config_one,
            headers={"x-api-key": user_one_api_key},
        )
        assert response.status_code == 200
        assert response.json() == config_one

        # User Two creates a server with the same name
        response = await client.post(
            f"/api/v2/mcp/servers/{server_name}",
            json=config_two,
            headers={"x-api-key": user_two_api_key},
        )
        assert response.status_code == 200
        assert response.json() == config_two

        # Verify each user gets their own server config
        response_one = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_one_api_key})
        assert response_one.status_code == 200
        assert response_one.json() == config_one

        response_two = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_two_api_key})
        assert response_two.status_code == 200
        assert response_two.json() == config_two

        # User One updates their server
        response = await client.patch(
            f"/api/v2/mcp/servers/{server_name}",
            json=updated_config_one,
            headers={"x-api-key": user_one_api_key},
        )
        assert response.status_code == 200
        assert response.json() == updated_config_one

        # Verify User One's server is updated and User Two's is not
        response_one = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_one_api_key})
        assert response_one.status_code == 200
        assert response_one.json() == updated_config_one

        response_two = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_two_api_key})
        assert response_two.status_code == 200
        assert response_two.json() == config_two, "User Two's server should not be affected by User One's update"

        # User One tries to delete User Two's server (should only delete their own)
        response = await client.delete(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_one_api_key})
        assert response.status_code == 200

        # Verify User One's server is deleted
        response_one = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_one_api_key})
        assert response_one.json() is None

        # Verify User Two's server still exists
        response_two = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_two_api_key})
        assert response_two.status_code == 200
        assert response_two.json() == config_two, "User Two's server should not be affected by User One's delete"

        # Cleanup: User Two deletes their server
        response = await client.delete(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_two_api_key})
        assert response.status_code == 200

        response_two = await client.get(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": user_two_api_key})
        assert response_two.json() is None