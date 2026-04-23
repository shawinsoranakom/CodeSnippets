async def test_list_resources(
    sample_resources: list[Resource], mock_mcp_actor: AsyncMock, sample_server_params: StdioServerParams
) -> None:
    """Test listing resources from MCP server."""
    # Create workbench
    workbench = McpWorkbench(server_params=sample_server_params)
    workbench._actor = mock_mcp_actor  # type: ignore[reportPrivateUsage]

    # Mock list_resources response
    list_resources_result = ListResourcesResult(resources=sample_resources)
    future_result: asyncio.Future[ListResourcesResult] = asyncio.Future()
    future_result.set_result(list_resources_result)
    mock_mcp_actor.call.return_value = future_result

    try:
        # List resources
        result = await workbench.list_resources()

        # Verify result
        assert isinstance(result, ListResourcesResult)
        assert len(result.resources) == 2
        assert str(result.resources[0].uri) == "file:///test/document.txt"
        assert result.resources[0].name == "Test Document"
        assert result.resources[0].mimeType == "text/plain"
        assert str(result.resources[1].uri) == "https://api.example.com/data"
        assert result.resources[1].name == "API Data"
        assert result.resources[1].mimeType == "application/json"

        # Verify actor was called correctly
        mock_mcp_actor.call.assert_called_with("list_resources", None)

    finally:
        workbench._actor = None