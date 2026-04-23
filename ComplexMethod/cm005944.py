def test_multiple_tools_conversion():
    """Test conversion of multiple tools at once."""
    tools = [MockBasicTool(), MockToolWithSchema()]
    result = PreToolValidationWrapper.convert_langchain_tools_to_sparc_tool_specs_format(tools)

    assert len(result) == 2

    # Check first tool (basic)
    basic_spec = result[0]
    assert basic_spec["function"]["name"] == "test_tool"
    # Basic tool should have query parameter as string
    assert "query" in basic_spec["function"]["parameters"]["properties"]
    assert basic_spec["function"]["parameters"]["properties"]["query"]["type"] == "string"

    # Check second tool (with schema)
    schema_spec = result[1]
    assert schema_spec["function"]["name"] == "fetch_content"
    assert "urls" in schema_spec["function"]["parameters"]["properties"]
    # Now correctly identifies as array
    assert schema_spec["function"]["parameters"]["properties"]["urls"]["type"] == "array"
    assert schema_spec["function"]["parameters"]["properties"]["urls"]["items"]["type"] == "string"