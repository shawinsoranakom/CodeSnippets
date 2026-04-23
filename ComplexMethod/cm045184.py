async def test_streamable_http_adapter_config_serialization(sample_streamable_http_tool: Tool) -> None:
    """Test that StreamableHttp adapter can be saved to and loaded from config."""
    params = StreamableHttpServerParams(url="http://test-url")
    original_adapter = StreamableHttpMcpToolAdapter(server_params=params, tool=sample_streamable_http_tool)
    config = original_adapter.dump_component()
    loaded_adapter = StreamableHttpMcpToolAdapter.load_component(config)

    # Test that the loaded adapter has the same properties
    assert loaded_adapter.name == "test_streamable_http_tool"
    assert loaded_adapter.description == "A test StreamableHttp tool"

    # Verify schema structure
    schema = loaded_adapter.schema
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