def test_tool_retry_specific_tools_with_base_tool() -> None:
    """Test ToolRetryMiddleware accepts BaseTool instances for filtering."""
    model = FakeToolCallingModel(
        tool_calls=[
            [
                ToolCall(name="failing_tool", args={"value": "test1"}, id="1"),
                ToolCall(name="working_tool", args={"value": "test2"}, id="2"),
            ],
            [],
        ]
    )

    # Only retry failing_tool, passed as BaseTool instance
    retry = ToolRetryMiddleware(
        max_retries=2,
        tools=[failing_tool],  # Pass BaseTool instance
        initial_delay=0.01,
        jitter=False,
        on_failure="continue",
    )

    agent = create_agent(
        model=model,
        tools=[failing_tool, working_tool],
        middleware=[retry],
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Use both tools")]},
        {"configurable": {"thread_id": "test"}},
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2

    # failing_tool should have error message (with retries)
    failing_msg = next(m for m in tool_messages if m.name == "failing_tool")
    assert failing_msg.status == "error"
    assert "3 attempts" in failing_msg.content

    # working_tool should succeed normally (no retry applied)
    working_msg = next(m for m in tool_messages if m.name == "working_tool")
    assert "Success: test2" in working_msg.content
    assert working_msg.status != "error"