async def test_actor_initialization() -> None:
    """Test actor initialization sets up correctly."""
    server_params = StdioServerParams(command="echo", args=["test"])

    # TODO: Add McpSessionHost
    actor = McpSessionActor(server_params)

    # Check initial state
    assert actor.server_params == server_params
    assert actor.name == "mcp_session_actor"
    assert actor.description == "MCP session actor"
    assert not actor._active  # type: ignore[reportPrivateUsage]
    assert actor._actor_task is None  # type: ignore[reportPrivateUsage]
    assert actor._shutdown_future is None  # type: ignore[reportPrivateUsage]
    assert actor._initialize_result is None