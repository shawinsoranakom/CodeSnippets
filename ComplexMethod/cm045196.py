async def test_actor_resource_operations(mcp_server_params: Any) -> None:
    """Test actor resource operations with real MCP server."""
    actor = McpSessionActor(mcp_server_params)

    try:
        await actor.initialize()
        await asyncio.sleep(0.1)

        # Test listing resources
        resources_future = await actor.call("list_resources")
        resources_result: mcp_types.ListResourcesResult = await resources_future  # type: ignore
        assert len(resources_result.resources) == 2  # users and projects
        resource_names = [resource.name for resource in resources_result.resources]
        assert "Company Users" in resource_names
        assert "Active Projects" in resource_names

        # Test reading a resource
        read_future = await actor.call("read_resource", {"name": None, "kargs": {"uri": "file:///company/users.json"}})
        read_result: mcp_types.ReadResourceResult = await read_future  # type: ignore
        users_data = json.loads(read_result.contents[0].text)  # type: ignore
        assert isinstance(users_data, list)
        assert len(users_data) == 3  # type: ignore[reportUnknownArgumentType]
        assert users_data[0]["name"] == "Alice"

    finally:
        await actor.close()