async def test_streamable_http_adapter_from_server_params(
    sample_streamable_http_tool: Tool,
    mock_streamable_http_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that StreamableHttp adapter can be created from server parameters."""
    params = StreamableHttpServerParams(url="http://test-url")
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_streamable_http_session
    monkeypatch.setattr(
        "autogen_ext.tools.mcp._base.create_mcp_server_session",
        lambda *args, **kwargs: mock_context,  # type: ignore
    )

    mock_streamable_http_session.list_tools.return_value.tools = [sample_streamable_http_tool]

    adapter = await StreamableHttpMcpToolAdapter.from_server_params(params, "test_streamable_http_tool")

    assert isinstance(adapter, StreamableHttpMcpToolAdapter)
    assert adapter.name == "test_streamable_http_tool"
    assert adapter.description == "A test StreamableHttp tool"

    # Verify schema structure
    schema = adapter.schema
    assert "parameters" in schema, "Schema must have parameters"
    params_schema = schema["parameters"]
    assert isinstance(params_schema, dict), "Parameters must be a dict"
    assert "type" in params_schema, "Parameters must have type"
    assert "required" in params_schema, "Parameters must have required fields"
    assert "properties" in params_schema, "Parameters must have properties"

    # Compare schema content
    assert params_schema["type"] == sample_streamable_http_tool.inputSchema["type"]
    assert params_schema["required"] == sample_streamable_http_tool.inputSchema["required"]
    assert (
        params_schema["properties"]["test_param"]["type"]
        == sample_streamable_http_tool.inputSchema["properties"]["test_param"]["type"]
    )