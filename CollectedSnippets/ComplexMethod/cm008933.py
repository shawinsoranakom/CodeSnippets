def test_config_and_runtime_not_injected_to_kwargs() -> None:
    """Config/runtime in args_schema are NOT injected when not in function signature."""
    captured: dict[str, Any] = {}

    def tool_func(**kwargs: Any) -> str:
        """Tool with only **kwargs."""
        captured["keys"] = list(kwargs.keys())
        captured["config"] = kwargs.get("config")
        captured["runtime"] = kwargs.get("runtime")
        captured["query"] = kwargs.get("query")
        return f"query={kwargs.get('query')}"

    tool = StructuredTool.from_function(
        func=tool_func,
        name="test_tool",
        description="Test tool",
        args_schema=ArgsSchema.model_json_schema(),
    )

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[[{"name": "test_tool", "args": {"query": "test"}, "id": "c1"}], []]
        ),
        tools=[tool],
        system_prompt="",
    )

    result = agent.invoke({"messages": [HumanMessage("hi")]})

    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == "query=test"

    # Only query passed - config/runtime NOT injected since not in function signature
    assert captured["keys"] == ["query"]
    assert captured["query"] == "test"
    assert captured["config"] is None
    assert captured["runtime"] is None