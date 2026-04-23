async def test_convert_tools() -> None:
    def add(x: int, y: Optional[int]) -> str:
        if y is None:
            return str(x)
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")

    tool_schema_noparam: ToolSchema = {
        "name": "manual_tool",
        "description": "A tool defined manually",
        "parameters": {
            "type": "object",
            "properties": {
                "param_with_type": {"type": "integer", "description": "An integer param"},
                "param_without_type": {"description": "A param without explicit type"},
            },
            "required": ["param_with_type"],
        },
    }

    converted_tools = convert_tools([add_tool, tool_schema_noparam])
    assert len(converted_tools) == 2
    assert isinstance(converted_tools[0].function, Tool.Function)
    assert isinstance(converted_tools[0].function.parameters, Tool.Function.Parameters)
    assert converted_tools[0].function.parameters.properties is not None
    assert converted_tools[0].function.name == add_tool.name
    assert converted_tools[0].function.parameters.properties["y"].type == "integer"

    # test it defaults to string
    assert isinstance(converted_tools[1].function, Tool.Function)
    assert isinstance(converted_tools[1].function.parameters, Tool.Function.Parameters)
    assert converted_tools[1].function.parameters.properties is not None
    assert converted_tools[1].function.name == "manual_tool"
    assert converted_tools[1].function.parameters.properties["param_with_type"].type == "integer"
    assert converted_tools[1].function.parameters.properties["param_without_type"].type == "string"
    assert converted_tools[1].function.parameters.required == ["param_with_type"]