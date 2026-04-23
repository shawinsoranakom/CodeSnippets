def test_tool_with_list_parameter():
    """Test conversion of a tool with list parameter type."""
    tool = MockToolWithSchema()

    # First validate that the tool has the correct schema before conversion
    assert hasattr(tool, "args_schema"), "Tool should have args_schema"
    schema_model = tool.args_schema
    assert issubclass(schema_model, BaseModel), "Schema should be a Pydantic model"

    # Check the schema field using Pydantic v2 model_fields
    schema_fields = schema_model.model_fields
    assert "urls" in schema_fields, "Schema should have urls field"
    urls_field = schema_fields["urls"]

    # Check that the field is properly configured
    assert not urls_field.is_required(), "urls field should be optional"
    assert urls_field.description == "Enter one or more URLs to crawl recursively, by clicking the '+' button."

    # Now test the conversion
    result = PreToolValidationWrapper.convert_langchain_tools_to_sparc_tool_specs_format([tool])

    assert len(result) == 1
    tool_spec = result[0]

    # Check basic structure
    assert tool_spec["type"] == "function", "Incorrect type"
    assert tool_spec["function"]["name"] == "fetch_content", "Incorrect name"
    assert (
        tool_spec["function"]["description"] == "Fetch content from one or more web pages, following links recursively."
    ), "Incorrect description"

    # Check parameters structure
    params = tool_spec["function"]["parameters"]
    assert params["type"] == "object", "Parameters should be an object"
    assert "properties" in params, "Parameters should have properties"
    assert isinstance(params["properties"], dict), "Properties should be a dictionary"

    # Check the urls parameter specifically
    assert "urls" in params["properties"], "urls parameter is missing"
    urls_spec = params["properties"]["urls"]
    logger.debug("Generated URLs spec: %s", urls_spec)  # Debug print

    # Now it should correctly identify as array type
    assert urls_spec["type"] == "array", "urls type should be array"
    assert urls_spec["description"] == "Enter one or more URLs to crawl recursively, by clicking the '+' button.", (
        "Incorrect urls description"
    )

    # Should have items specification
    assert "items" in urls_spec, "Array should have items specification"
    assert urls_spec["items"]["type"] == "string", "Array items should be strings"

    # Should have default value since it's optional
    assert urls_spec.get("default") is None, "Should have default None value"

    # Since urls is optional, it should not be in required list
    assert "required" in params, "Parameters should have required field"
    assert isinstance(params["required"], list), "Required should be a list"
    assert "urls" not in params["required"], "urls should not be in required list"