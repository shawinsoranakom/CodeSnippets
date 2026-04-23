async def test_tool_runtime_parallel_execution() -> None:
    """Test ToolRuntime injection works with parallel tool execution."""
    execution_log = []

    @tool
    async def parallel_tool_1(x: int, runtime: ToolRuntime) -> str:
        """First parallel tool."""
        execution_log.append(("tool_1", runtime.tool_call_id, x))
        return f"Tool1: {x}"

    @tool
    async def parallel_tool_2(y: int, runtime: ToolRuntime) -> str:
        """Second parallel tool."""
        execution_log.append(("tool_2", runtime.tool_call_id, y))
        return f"Tool2: {y}"

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [
                    {"args": {"x": 10}, "id": "parallel_1", "name": "parallel_tool_1"},
                    {"args": {"y": 20}, "id": "parallel_2", "name": "parallel_tool_2"},
                ],
                [],
            ]
        ),
        tools=[parallel_tool_1, parallel_tool_2],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke({"messages": [HumanMessage("Run parallel")]})

    # Verify both tools executed
    assert len(execution_log) == 2

    # Find the tool messages (order may vary due to parallel execution)
    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 2

    contents = {msg.content for msg in tool_messages}
    assert "Tool1: 10" in contents
    assert "Tool2: 20" in contents

    call_ids = {msg.tool_call_id for msg in tool_messages}
    assert "parallel_1" in call_ids
    assert "parallel_2" in call_ids