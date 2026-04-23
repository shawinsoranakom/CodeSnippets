def test_tool_retry_failing_tool_returns_message() -> None:
    """Test ToolRetryMiddlewarewith failing tool returns error message."""
    model = FakeToolCallingModel(
        tool_calls=[
            [ToolCall(name="failing_tool", args={"value": "test"}, id="1")],
            [],
        ]
    )

    retry = ToolRetryMiddleware(
        max_retries=2,
        initial_delay=0.01,
        jitter=False,
        on_failure="continue",
    )

    agent = create_agent(
        model=model,
        tools=[failing_tool],
        middleware=[retry],
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Use failing tool")]},
        {"configurable": {"thread_id": "test"}},
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    # Should contain error message with tool name and attempts
    assert "failing_tool" in tool_messages[0].content
    assert "3 attempts" in tool_messages[0].content
    assert "ValueError" in tool_messages[0].content
    assert tool_messages[0].status == "error"