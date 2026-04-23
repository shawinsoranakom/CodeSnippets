def test_tool_runtime_basic_injection() -> None:
    """Test basic ToolRuntime injection in tools with create_agent."""
    # Track what was injected
    injected_data: dict[str, Any] = {}

    @tool
    def runtime_tool(x: int, runtime: ToolRuntime) -> str:
        """Tool that accesses runtime context."""
        injected_data["state"] = runtime.state
        injected_data["tool_call_id"] = runtime.tool_call_id
        injected_data["config"] = runtime.config
        injected_data["context"] = runtime.context
        injected_data["store"] = runtime.store
        injected_data["stream_writer"] = runtime.stream_writer
        return f"Processed {x}"

    assert runtime_tool.args

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [{"args": {"x": 42}, "id": "call_123", "name": "runtime_tool"}],
                [],
            ]
        ),
        tools=[runtime_tool],
        system_prompt="You are a helpful assistant.",
    )

    result = agent.invoke({"messages": [HumanMessage("Test")]})

    # Verify tool executed
    assert len(result["messages"]) == 4
    tool_message = result["messages"][2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == "Processed 42"
    assert tool_message.tool_call_id == "call_123"

    # Verify runtime was injected
    assert injected_data["state"] is not None
    assert "messages" in injected_data["state"]
    assert injected_data["tool_call_id"] == "call_123"
    assert injected_data["config"] is not None
    # Context, store, stream_writer may be None depending on graph setup
    assert "context" in injected_data
    assert "store" in injected_data
    assert "stream_writer" in injected_data