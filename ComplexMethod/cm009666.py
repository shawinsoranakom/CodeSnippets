def test_tool_decorator_description() -> None:
    # test basic tool
    @tool
    def foo(x: int) -> str:
        """Foo."""
        return "hi"

    assert foo.description == "Foo."
    assert (
        cast("BaseModel", foo.tool_call_schema).model_json_schema()["description"]
        == "Foo."
    )

    # test basic tool with description
    @tool(description="description")
    def foo_description(x: int) -> str:
        """Foo."""
        return "hi"

    assert foo_description.description == "description"
    assert (
        cast("BaseModel", foo_description.tool_call_schema).model_json_schema()[
            "description"
        ]
        == "description"
    )

    # test tool with args schema
    class ArgsSchema(BaseModel):
        """Bar."""

        x: int

    @tool(args_schema=ArgsSchema)
    def foo_args_schema(x: int) -> str:
        return "hi"

    assert foo_args_schema.description == "Bar."
    assert (
        cast("BaseModel", foo_args_schema.tool_call_schema).model_json_schema()[
            "description"
        ]
        == "Bar."
    )

    @tool(description="description", args_schema=ArgsSchema)
    def foo_args_schema_description(x: int) -> str:
        return "hi"

    assert foo_args_schema_description.description == "description"
    assert (
        cast(
            "BaseModel", foo_args_schema_description.tool_call_schema
        ).model_json_schema()["description"]
        == "description"
    )

    args_json_schema = {
        "description": "JSON Schema.",
        "properties": {
            "x": {"description": "my field", "title": "X", "type": "string"}
        },
        "required": ["x"],
        "title": "my_tool",
        "type": "object",
    }

    @tool(args_schema=args_json_schema)
    def foo_args_jsons_schema(x: int) -> str:
        return "hi"

    @tool(description="description", args_schema=args_json_schema)
    def foo_args_jsons_schema_with_description(x: int) -> str:
        return "hi"

    assert foo_args_jsons_schema.description == "JSON Schema."
    assert (
        cast("dict[str, Any]", foo_args_jsons_schema.tool_call_schema)["description"]
        == "JSON Schema."
    )

    assert foo_args_jsons_schema_with_description.description == "description"
    assert (
        cast("dict[str, Any]", foo_args_jsons_schema_with_description.tool_call_schema)[
            "description"
        ]
        == "description"
    )