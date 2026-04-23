async def test_tool_runtime_async_injection() -> None:
    """Test ToolRuntime injection works with async tools."""
    injected_data: dict[str, Any] = {}

    @tool
    async def async_runtime_tool(x: int, runtime: ToolRuntime) -> str:
        """Async tool that accesses runtime context."""
        injected_data["state"] = runtime.state
        injected_data["tool_call_id"] = runtime.tool_call_id
        injected_data["config"] = runtime.config
        return f"Async processed {x}"

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [{"args": {"x": 99}, "id": "async_call_456", "name": "async_runtime_tool"}],
                [],
            ]
        ),
        tools=[async_runtime_tool],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke({"messages": [HumanMessage("Test async")]})

    # Verify tool executed
    assert len(result["messages"]) == 4
    tool_message = result["messages"][2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == "Async processed 99"
    assert tool_message.tool_call_id == "async_call_456"

    # Verify runtime was injected
    assert injected_data["state"] is not None
    assert "messages" in injected_data["state"]
    assert injected_data["tool_call_id"] == "async_call_456"
    assert injected_data["config"] is not None