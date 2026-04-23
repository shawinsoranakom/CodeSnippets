def test_tool_schema_generation() -> None:
    schema = MyTool().schema

    assert schema["name"] == "TestTool"
    assert "description" in schema
    assert schema["description"] == "Description of test tool."
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert "properties" in schema["parameters"]
    assert schema["parameters"]["properties"]["query"]["description"] == "The description."
    assert schema["parameters"]["properties"]["query"]["type"] == "string"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == ["query"]
    assert len(schema["parameters"]["properties"]) == 1