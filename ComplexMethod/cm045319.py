def test_nested_tool_schema_generation() -> None:
    schema: ToolSchema = MyNestedTool().schema

    assert "description" in schema
    assert "parameters" in schema
    assert "type" in schema["parameters"]
    assert "arg" in schema["parameters"]["properties"]
    assert "type" in schema["parameters"]["properties"]["arg"]
    assert "title" in schema["parameters"]["properties"]["arg"]
    assert "properties" in schema["parameters"]["properties"]["arg"]
    assert "query" in schema["parameters"]["properties"]["arg"]["properties"]
    assert "type" in schema["parameters"]["properties"]["arg"]["properties"]["query"]
    assert "description" in schema["parameters"]["properties"]["arg"]["properties"]["query"]
    assert "required" in schema["parameters"]
    assert schema["description"] == "Description of test nested tool."
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"]["arg"]["type"] == "object"
    assert schema["parameters"]["properties"]["arg"]["title"] == "MyArgs"
    assert schema["parameters"]["properties"]["arg"]["properties"]["query"]["type"] == "string"
    assert schema["parameters"]["properties"]["arg"]["properties"]["query"]["description"] == "The description."
    assert schema["parameters"]["properties"]["arg"]["required"] == ["query"]
    assert schema["parameters"]["required"] == ["arg"]
    assert len(schema["parameters"]["properties"]) == 1