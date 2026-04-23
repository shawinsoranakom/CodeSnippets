def test_tool_properties(test_config: ComponentModel) -> None:
    tool = HttpTool.load_component(test_config)

    assert tool.name == "TestHttpTool"
    assert tool.description == "A test HTTP tool"
    assert tool.server_params.host == "localhost"
    assert tool.server_params.port == 8000
    assert tool.server_params.path == "/test"
    assert tool.server_params.scheme == "http"
    assert tool.server_params.method == "POST"