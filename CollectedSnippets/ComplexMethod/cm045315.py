def test_func_tool_schema_generation_only_default_arg() -> None:
    def my_function(arg: str = "default") -> MyResult:
        return MyResult(result="test")

    tool = FunctionTool(my_function, description="Function tool.")
    schema = tool.schema

    assert schema["name"] == "my_function"
    assert "description" in schema
    assert schema["description"] == "Function tool."
    assert "parameters" in schema
    assert len(schema["parameters"]["properties"]) == 1
    assert schema["parameters"]["properties"]["arg"]["type"] == "string"
    assert schema["parameters"]["properties"]["arg"]["description"] == "arg"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == []