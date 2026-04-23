def test_tool_schema_generation(test_config: ComponentModel) -> None:
    tool = HttpTool.load_component(test_config)
    schema = tool.schema

    assert schema["name"] == "TestHttpTool"
    assert "description" in schema
    assert schema["description"] == "A test HTTP tool"
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert "properties" in schema["parameters"]
    assert schema["parameters"]["properties"]["query"]["description"] == "The test query"
    assert schema["parameters"]["properties"]["query"]["type"] == "string"
    assert schema["parameters"]["properties"]["value"]["description"] == "A test value"
    assert schema["parameters"]["properties"]["value"]["type"] == "integer"
    assert "required" in schema["parameters"]
    assert set(schema["parameters"]["required"]) == {"query", "value"}