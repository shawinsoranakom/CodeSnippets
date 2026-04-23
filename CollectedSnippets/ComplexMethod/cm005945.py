def test_complex_schema_conversion():
    """Test conversion of tools with complex parameter schemas."""
    from pydantic import BaseModel, Field

    class ComplexSchema(BaseModel):
        required_str: str = Field(description="A required string parameter")
        optional_int: int | None = Field(default=None, description="An optional integer")
        str_list: list[str] = Field(default_factory=list, description="A list of strings")

    class ComplexTool(BaseTool):
        name: str = "complex_tool"
        description: str = "A tool with complex parameters"
        args_schema: type[BaseModel] = ComplexSchema

        def _run(self, **kwargs):
            logger.debug(f"ComplexTool called with kwargs: {kwargs}")
            return "complex result"

    tool = ComplexTool()
    result = PreToolValidationWrapper.convert_langchain_tools_to_sparc_tool_specs_format([tool])

    assert len(result) == 1
    tool_spec = result[0]

    # Check that all parameters are properly converted
    props = tool_spec["function"]["parameters"]["properties"]

    # Required string parameter
    assert "required_str" in props
    assert props["required_str"]["type"] == "string"
    assert props["required_str"]["description"] == "A required string parameter"

    # Optional integer parameter
    assert "optional_int" in props
    # Should handle the Union[int, None] properly
    assert props["optional_int"]["type"] == "integer"
    assert props["optional_int"]["description"] == "An optional integer"

    # List parameter
    assert "str_list" in props
    assert props["str_list"]["type"] == "array"
    assert props["str_list"]["description"] == "A list of strings"
    assert props["str_list"]["items"]["type"] == "string"

    # Check required fields
    required = tool_spec["function"]["parameters"]["required"]
    assert "required_str" in required
    assert "optional_int" not in required  # Should not be required
    assert "str_list" not in required