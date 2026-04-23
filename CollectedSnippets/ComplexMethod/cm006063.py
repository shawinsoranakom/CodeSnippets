async def test_init_mcp_servers(user_test_project, other_test_project):
    """Test the initialization of MCP servers for all projects."""
    # Clear existing caches
    project_sse_transports.clear()
    project_mcp_servers.clear()

    # Test the initialization function
    await init_mcp_servers()

    # Verify that both test projects have SSE transports and MCP servers initialized
    project1_id = str(user_test_project.id)
    project2_id = str(other_test_project.id)

    # Both projects should have SSE transports created
    assert project1_id in project_sse_transports
    assert project2_id in project_sse_transports

    # Both projects should have MCP servers created
    assert project1_id in project_mcp_servers
    assert project2_id in project_mcp_servers

    # Verify the correct configuration
    assert isinstance(project_sse_transports[project1_id], SseServerTransport)
    assert isinstance(project_sse_transports[project2_id], SseServerTransport)
    assert isinstance(project_mcp_servers[project1_id], ProjectMCPServer)
    assert isinstance(project_mcp_servers[project2_id], ProjectMCPServer)

    assert project_mcp_servers[project1_id].project_id == user_test_project.id
    assert project_mcp_servers[project2_id].project_id == other_test_project.id