async def test_sse_adapter_from_server_params(
    sample_sse_tool: Tool,
    mock_sse_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that SSE adapter can be created from server parameters."""
    params = SseServerParams(url="http://test-url")
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_sse_session
    monkeypatch.setattr(
        "autogen_ext.tools.mcp._base.create_mcp_server_session",
        lambda *args, **kwargs: mock_context,  # type: ignore
    )

    mock_sse_session.list_tools.return_value.tools = [sample_sse_tool]

    adapter = await SseMcpToolAdapter.from_server_params(params, "test_sse_tool")

    assert isinstance(adapter, SseMcpToolAdapter)
    assert adapter.name == "test_sse_tool"
    assert adapter.description == "A test SSE tool"

    # Verify schema structure
    schema = adapter.schema
    assert "parameters" in schema, "Schema must have parameters"
    params_schema = schema["parameters"]
    assert isinstance(params_schema, dict), "Parameters must be a dict"
    assert "type" in params_schema, "Parameters must have type"
    assert "required" in params_schema, "Parameters must have required fields"
    assert "properties" in params_schema, "Parameters must have properties"

    # Compare schema content
    assert params_schema["type"] == sample_sse_tool.inputSchema["type"]
    assert params_schema["required"] == sample_sse_tool.inputSchema["required"]
    assert (
        params_schema["properties"]["test_param"]["type"]
        == sample_sse_tool.inputSchema["properties"]["test_param"]["type"]
    )