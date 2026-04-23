async def test_list_resource_templates(
    sample_resource_templates: list[ResourceTemplate],
    mock_mcp_actor: AsyncMock,
    sample_server_params: StdioServerParams,
) -> None:
    """Test listing resource templates from MCP server."""
    # Create workbench
    workbench = McpWorkbench(server_params=sample_server_params)
    workbench._actor = mock_mcp_actor  # type: ignore[reportPrivateUsage]

    # Mock list_resource_templates response
    list_templates_result = ListResourceTemplatesResult(resourceTemplates=sample_resource_templates)
    future_result: asyncio.Future[ListResourceTemplatesResult] = asyncio.Future()
    future_result.set_result(list_templates_result)
    mock_mcp_actor.call.return_value = future_result

    try:
        # List resource templates
        result = await workbench.list_resource_templates()

        # Verify result
        assert isinstance(result, ListResourceTemplatesResult)
        assert len(result.resourceTemplates) == 2
        assert result.resourceTemplates[0].uriTemplate == "file:///logs/{date}.log"
        assert result.resourceTemplates[0].name == "Daily Logs"
        assert result.resourceTemplates[0].mimeType == "text/plain"
        assert result.resourceTemplates[1].uriTemplate == "https://api.example.com/users/{userId}"
        assert result.resourceTemplates[1].name == "User Profile"
        assert result.resourceTemplates[1].mimeType == "application/json"

        # Verify actor was called correctly
        mock_mcp_actor.call.assert_called_with("list_resource_templates", None)

    finally:
        workbench._actor = None