def test_tool_runtime_with_multiple_tools() -> None:
    """Test multiple tools can all access ToolRuntime."""
    call_log: list[tuple[str, str | None, int | str]] = []

    @tool
    def tool_a(x: int, runtime: ToolRuntime) -> str:
        """First tool."""
        call_log.append(("tool_a", runtime.tool_call_id, x))
        return f"A: {x}"

    @tool
    def tool_b(y: str, runtime: ToolRuntime) -> str:
        """Second tool."""
        call_log.append(("tool_b", runtime.tool_call_id, y))
        return f"B: {y}"

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [
                    {"args": {"x": 1}, "id": "call_a", "name": "tool_a"},
                    {"args": {"y": "test"}, "id": "call_b", "name": "tool_b"},
                ],
                [],
            ]
        ),
        tools=[tool_a, tool_b],
        system_prompt="You are a helpful assistant.",
    )

    result = agent.invoke({"messages": [HumanMessage("Use both tools")]})

    # Verify both tools were called with correct runtime
    assert len(call_log) == 2
    # Tools may execute in parallel, so check both calls are present
    call_ids = {(name, call_id) for name, call_id, _ in call_log}
    assert ("tool_a", "call_a") in call_ids
    assert ("tool_b", "call_b") in call_ids

    # Verify tool messages
    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 2
    contents = {msg.content for msg in tool_messages}
    assert "A: 1" in contents
    assert "B: test" in contents