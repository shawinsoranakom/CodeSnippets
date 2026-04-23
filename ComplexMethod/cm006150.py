async def test_validate_server_exists_project_doesnt_match(
        self, active_user, test_project, created_api_key, client: AsyncClient, transport
    ):
        """Test validation when server exists but project ID doesn't match."""
        other_project_id = uuid4()
        server_name = "lf-test_project"
        _, server_config = _build_server_config(client.base_url, other_project_id, transport)

        # Create MCP server with different project ID via API
        response = await client.post(
            f"/api/v2/mcp/servers/{server_name}", json=server_config, headers={"x-api-key": created_api_key.api_key}
        )
        assert response.status_code == 200

        from langflow.services.deps import get_settings_service, get_storage_service

        async with session_scope() as session:
            storage_service = get_storage_service()
            settings_service = get_settings_service()

            result = await validate_mcp_server_for_project(
                test_project.id, test_project.name, active_user, session, storage_service, settings_service, "create"
            )

            assert result.server_exists is True
            assert result.project_id_matches is False
            assert result.server_name == server_name
            assert result.existing_config == server_config
            assert "MCP server name conflict" in result.conflict_message
            assert str(test_project.id) in result.conflict_message

        # Cleanup - delete the server
        await client.delete(f"/api/v2/mcp/servers/{server_name}", headers={"x-api-key": created_api_key.api_key})