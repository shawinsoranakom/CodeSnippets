def test_tool_retry_deprecated_return_message_behavior() -> None:
    """Test ToolRetryMiddleware with deprecated 'return_message' forwards to 'continue' behavior."""
    model = FakeToolCallingModel(
        tool_calls=[
            [ToolCall(name="failing_tool", args={"value": "test"}, id="1")],
            [],
        ]
    )

    # Use string concatenation to avoid batch replace affecting test code
    deprecated_value = "return" + "_message"
    with pytest.warns(DeprecationWarning, match="on_failure='return_message' is deprecated"):
        retry = ToolRetryMiddleware(
            max_retries=2,
            initial_delay=0.01,
            jitter=False,
            on_failure=deprecated_value,  # type: ignore[arg-type]
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
    # Should contain error message (same as 'continue')
    assert "failing_tool" in tool_messages[0].content
    assert "3 attempts" in tool_messages[0].content
    assert "ValueError" in tool_messages[0].content
    assert tool_messages[0].status == "error"