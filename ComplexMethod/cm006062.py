async def test_project_sse_creation(user_test_project):
    """Test that SSE transport and MCP server are correctly created for a project."""
    # Test getting an SSE transport for the first time
    project_id = user_test_project.id
    project_id_str = str(project_id)

    # Ensure there's no SSE transport for this project yet
    if project_id_str in project_sse_transports:
        del project_sse_transports[project_id_str]

    # Get an SSE transport
    sse_transport = get_project_sse(project_id)

    # Verify the transport was created correctly
    assert project_id_str in project_sse_transports
    assert sse_transport is project_sse_transports[project_id_str]
    assert isinstance(sse_transport, SseServerTransport)

    # Test getting an MCP server for the first time
    if project_id_str in project_mcp_servers:
        del project_mcp_servers[project_id_str]

    # Get an MCP server
    mcp_server = get_project_mcp_server(project_id)

    # Verify the server was created correctly
    assert project_id_str in project_mcp_servers
    assert mcp_server is project_mcp_servers[project_id_str]
    assert isinstance(mcp_server, ProjectMCPServer)
    assert mcp_server.project_id == project_id
    assert mcp_server.server.name == f"langflow-mcp-project-{project_id}"

    # Test that getting the same SSE transport and MCP server again returns the cached instances
    sse_transport2 = get_project_sse(project_id)
    mcp_server2 = get_project_mcp_server(project_id)

    assert sse_transport2 is sse_transport
    assert mcp_server2 is mcp_server
    # Yield control to the event loop to satisfy async usage in this test
    await asyncio.sleep(0)