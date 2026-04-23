def test_func_tool_schema_generation_strict() -> None:
    def my_function1(arg: str, other: Annotated[int, "int arg"], nonrequired: int = 5) -> MyResult:
        return MyResult(result="test")

    with pytest.raises(ValueError, match="Strict mode is enabled"):
        tool = FunctionTool(my_function1, description="Function tool.", strict=True)
        schema = tool.schema

    def my_function2(arg: str, other: Annotated[int, "int arg"]) -> MyResult:
        return MyResult(result="test")

    tool = FunctionTool(my_function2, description="Function tool.", strict=True)
    schema = tool.schema

    assert schema["name"] == "my_function2"
    assert "description" in schema
    assert schema["description"] == "Function tool."
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"].keys() == {"arg", "other"}
    assert schema["parameters"]["properties"]["arg"]["type"] == "string"
    assert schema["parameters"]["properties"]["arg"]["description"] == "arg"
    assert schema["parameters"]["properties"]["other"]["type"] == "integer"
    assert schema["parameters"]["properties"]["other"]["description"] == "int arg"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == ["arg", "other"]
    assert len(schema["parameters"]["properties"]) == 2
    assert "additionalProperties" in schema["parameters"]
    assert schema["parameters"]["additionalProperties"] is False