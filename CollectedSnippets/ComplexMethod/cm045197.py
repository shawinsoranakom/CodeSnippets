async def test_actor(mcp_server_params: Any) -> None:
    """Test actor with real MCP server subprocess."""
    actor = McpSessionActor(mcp_server_params)

    try:
        # Initialize the actor
        await actor.initialize()
        assert actor._active  # type: ignore[reportPrivateUsage]
        assert actor._actor_task is not None  # type: ignore[reportPrivateUsage]

        # Test listing tools
        tools_future = await actor.call("list_tools")
        tools_result: mcp_types.ListToolsResult = await tools_future  # type: ignore
        expected_tool_count = await get_expected_tool_count()
        assert len(tools_result.tools) == expected_tool_count
        tool_names = [tool.name for tool in tools_result.tools]
        assert "echo" in tool_names
        assert "get_time" in tool_names

        # Test calling the echo tool
        call_future = await actor.call("call_tool", {"name": "echo", "kargs": {"text": "Hello World"}})
        call_result: mcp_types.CallToolResult = await call_future  # type: ignore
        assert call_result.content[0].text == "Echo: Hello World"  # type: ignore

        # Test calling the get_time tool
        time_future = await actor.call("call_tool", {"name": "get_time", "kargs": {}})
        time_result: mcp_types.CallToolResult = await time_future  # type: ignore
        assert "Current time:" in time_result.content[0].text  # type: ignore

    finally:
        await actor.close()