def test_func_tool_schema_generation() -> None:
    def my_function(arg: str, other: Annotated[int, "int arg"], nonrequired: int = 5) -> MyResult:
        return MyResult(result="test")

    tool = FunctionTool(my_function, description="Function tool.")
    schema = tool.schema

    assert schema["name"] == "my_function"
    assert "description" in schema
    assert schema["description"] == "Function tool."
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"].keys() == {"arg", "other", "nonrequired"}
    assert schema["parameters"]["properties"]["arg"]["type"] == "string"
    assert schema["parameters"]["properties"]["arg"]["description"] == "arg"
    assert schema["parameters"]["properties"]["other"]["type"] == "integer"
    assert schema["parameters"]["properties"]["other"]["description"] == "int arg"
    assert schema["parameters"]["properties"]["nonrequired"]["type"] == "integer"
    assert schema["parameters"]["properties"]["nonrequired"]["description"] == "nonrequired"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == ["arg", "other"]
    assert len(schema["parameters"]["properties"]) == 3