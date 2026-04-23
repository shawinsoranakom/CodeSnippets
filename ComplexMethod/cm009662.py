def test_convert_from_runnable_dict() -> None:
    # Test with typed dict input
    class Args(TypedDict):
        a: int
        b: list[int]

    def f(x: Args) -> str:
        return str(x["a"] * max(x["b"]))

    runnable = RunnableLambda(f)
    as_tool = runnable.as_tool()
    args_schema = as_tool.args_schema
    assert args_schema is not None
    assert _schema(args_schema) == {
        "title": "f",
        "type": "object",
        "properties": {
            "a": {"title": "A", "type": "integer"},
            "b": {"title": "B", "type": "array", "items": {"type": "integer"}},
        },
        "required": ["a", "b"],
    }
    assert as_tool.description
    result = as_tool.invoke({"a": 3, "b": [1, 2]})
    assert result == "6"

    as_tool = runnable.as_tool(name="my tool", description="test description")
    assert as_tool.name == "my tool"
    assert as_tool.description == "test description"

    # Dict without typed input-- must supply schema
    def g(x: dict[str, Any]) -> str:
        return str(x["a"] * max(x["b"]))

    # Specify via args_schema:
    class GSchema(BaseModel):
        """Apply a function to an integer and list of integers."""

        a: int = Field(..., description="Integer")
        b: list[int] = Field(..., description="List of ints")

    runnable2 = RunnableLambda(g)
    as_tool2 = runnable2.as_tool(GSchema)
    as_tool2.invoke({"a": 3, "b": [1, 2]})

    # Specify via arg_types:
    runnable3 = RunnableLambda(g)
    as_tool3 = runnable3.as_tool(arg_types={"a": int, "b": list[int]})
    result = as_tool3.invoke({"a": 3, "b": [1, 2]})
    assert result == "6"

    # Test with config
    def h(x: dict[str, Any]) -> str:
        config = ensure_config()
        assert config["configurable"]["foo"] == "not-bar"
        return str(x["a"] * max(x["b"]))

    runnable4 = RunnableLambda(h)
    as_tool4 = runnable4.as_tool(arg_types={"a": int, "b": list[int]})
    result = as_tool4.invoke(
        {"a": 3, "b": [1, 2]}, config={"configurable": {"foo": "not-bar"}}
    )
    assert result == "6"