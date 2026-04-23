async def test_list_project_tools_with_mcp_enabled_filter(
    client: AsyncClient, user_test_project, active_user, logged_in_headers
):
    """Test that the list_project_tools endpoint correctly filters by mcp_enabled parameter."""
    # Create two flows: one with mcp_enabled=True and one with mcp_enabled=False
    enabled_flow_id = uuid4()
    disabled_flow_id = uuid4()

    async with session_scope() as session:
        # Create an MCP-enabled flow
        enabled_flow = Flow(
            id=enabled_flow_id,
            name="Enabled Flow",
            description="This flow is MCP enabled",
            mcp_enabled=True,
            action_name="enabled_action",
            action_description="Enabled action description",
            folder_id=user_test_project.id,
            user_id=active_user.id,
        )
        # Create an MCP-disabled flow
        disabled_flow = Flow(
            id=disabled_flow_id,
            name="Disabled Flow",
            description="This flow is MCP disabled",
            mcp_enabled=False,
            action_name="disabled_action",
            action_description="Disabled action description",
            folder_id=user_test_project.id,
            user_id=active_user.id,
        )
        session.add(enabled_flow)
        session.add(disabled_flow)
        await session.flush()

    try:
        # Test 1: With mcp_enabled=True (default), should only return enabled flows
        response = await client.get(
            f"/api/v1/mcp/project/{user_test_project.id}",
            headers=logged_in_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        tools = data["tools"]
        # Should only include the enabled flow
        assert len(tools) == 1
        assert tools[0]["name"] == "Enabled Flow"
        assert tools[0]["action_name"] == "enabled_action"

        # Test 2: With mcp_enabled=True explicitly, should only return enabled flows
        response = await client.get(
            f"/api/v1/mcp/project/{user_test_project.id}?mcp_enabled=true",
            headers=logged_in_headers,
        )
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "Enabled Flow"

        # Test 3: With mcp_enabled=False, should return all flows
        response = await client.get(
            f"/api/v1/mcp/project/{user_test_project.id}?mcp_enabled=false",
            headers=logged_in_headers,
        )
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        # Should include both flows
        assert len(tools) == 2
        flow_names = {tool["name"] for tool in tools}
        assert "Enabled Flow" in flow_names
        assert "Disabled Flow" in flow_names

    finally:
        # Clean up flows
        async with session_scope() as session:
            enabled_flow = await session.get(Flow, enabled_flow_id)
            if enabled_flow:
                await session.delete(enabled_flow)
            disabled_flow = await session.get(Flow, disabled_flow_id)
            if disabled_flow:
                await session.delete(disabled_flow)