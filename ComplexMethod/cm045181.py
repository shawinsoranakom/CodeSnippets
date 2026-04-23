async def test_adapter_from_server_params(
    sample_tool: Tool,
    sample_server_params: StdioServerParams,
    mock_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that adapter can be created from server parameters."""
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    monkeypatch.setattr(
        "autogen_ext.tools.mcp._base.create_mcp_server_session",
        lambda *args, **kwargs: mock_context,  # type: ignore
    )

    mock_session.list_tools.return_value.tools = [sample_tool]

    adapter = await StdioMcpToolAdapter.from_server_params(sample_server_params, "test_tool")

    assert isinstance(adapter, StdioMcpToolAdapter)
    assert adapter.name == "test_tool"
    assert adapter.description == "A test tool"

    # Verify schema structure
    schema = adapter.schema
    assert "parameters" in schema, "Schema must have parameters"
    params_schema = schema["parameters"]
    assert isinstance(params_schema, dict), "Parameters must be a dict"
    assert "type" in params_schema, "Parameters must have type"
    assert "required" in params_schema, "Parameters must have required fields"
    assert "properties" in params_schema, "Parameters must have properties"

    # Compare schema content
    assert params_schema["type"] == sample_tool.inputSchema["type"]
    assert params_schema["required"] == sample_tool.inputSchema["required"]
    assert (
        params_schema["properties"]["test_param"]["type"] == sample_tool.inputSchema["properties"]["test_param"]["type"]
    )