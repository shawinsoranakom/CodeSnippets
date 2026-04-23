def test_structured_tool_with_different_pydantic_versions(pydantic_model: Any) -> None:
    """This should test that one can type the args schema as a Pydantic model."""

    def foo(a: int, b: str) -> str:
        """Hahaha."""
        return "foo"

    foo_tool = StructuredTool.from_function(
        func=foo,
        args_schema=pydantic_model,
    )

    assert foo_tool.invoke({"a": 5, "b": "hello"}) == "foo"

    args_schema = cast("type[BaseModel]", foo_tool.args_schema)
    if issubclass(args_schema, BaseModel):
        args_json_schema = args_schema.model_json_schema()
    elif issubclass(args_schema, BaseModelV1):
        args_json_schema = args_schema.schema()
    else:
        msg = "Unknown input schema type"
        raise TypeError(msg)
    assert args_json_schema == {
        "properties": {
            "a": {"title": "A", "type": "integer"},
            "b": {"title": "B", "type": "string"},
        },
        "required": ["a", "b"],
        "title": pydantic_model.__name__,
        "type": "object",
    }

    input_schema = foo_tool.get_input_schema()
    if issubclass(input_schema, BaseModel):
        input_json_schema = input_schema.model_json_schema()
    elif issubclass(input_schema, BaseModelV1):
        input_json_schema = input_schema.schema()
    else:
        msg = "Unknown input schema type"
        raise TypeError(msg)
    assert input_json_schema == {
        "properties": {
            "a": {"title": "A", "type": "integer"},
            "b": {"title": "B", "type": "string"},
        },
        "required": ["a", "b"],
        "title": pydantic_model.__name__,
        "type": "object",
    }