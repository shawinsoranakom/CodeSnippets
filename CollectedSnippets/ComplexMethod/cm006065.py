async def test_list_project_tools_response_structure(client: AsyncClient, user_test_project, logged_in_headers):
    """Test that the list_project_tools endpoint returns the correct MCPProjectResponse structure."""
    response = await client.get(
        f"/api/v1/mcp/project/{user_test_project.id}",
        headers=logged_in_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure matches MCPProjectResponse
    assert "tools" in data
    assert "auth_settings" in data
    assert isinstance(data["tools"], list)

    # Verify tool structure
    if len(data["tools"]) > 0:
        tool = data["tools"][0]
        assert "id" in tool
        assert "name" in tool
        assert "description" in tool
        assert "action_name" in tool
        assert "action_description" in tool
        assert "mcp_enabled" in tool