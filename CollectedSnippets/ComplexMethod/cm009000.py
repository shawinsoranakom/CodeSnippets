def test_tool_retry_specific_exceptions() -> None:
    """Test ToolRetryMiddlewareonly retries specific exception types."""

    @tool
    def value_error_tool(value: str) -> str:
        """Tool that raises ValueError."""
        msg = f"ValueError: {value}"
        raise ValueError(msg)

    @tool
    def runtime_error_tool(value: str) -> str:
        """Tool that raises RuntimeError."""
        msg = f"RuntimeError: {value}"
        raise RuntimeError(msg)

    model = FakeToolCallingModel(
        tool_calls=[
            [
                ToolCall(name="value_error_tool", args={"value": "test1"}, id="1"),
                ToolCall(name="runtime_error_tool", args={"value": "test2"}, id="2"),
            ],
            [],
        ]
    )

    # Only retry ValueError
    retry = ToolRetryMiddleware(
        max_retries=2,
        retry_on=(ValueError,),
        initial_delay=0.01,
        jitter=False,
        on_failure="continue",
    )

    agent = create_agent(
        model=model,
        tools=[value_error_tool, runtime_error_tool],
        middleware=[retry],
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Use both tools")]},
        {"configurable": {"thread_id": "test"}},
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2

    # ValueError should be retried (3 attempts)
    value_error_msg = next(m for m in tool_messages if m.name == "value_error_tool")
    assert "3 attempts" in value_error_msg.content

    # RuntimeError should fail immediately (1 attempt only)
    runtime_error_msg = next(m for m in tool_messages if m.name == "runtime_error_tool")
    assert "1 attempt" in runtime_error_msg.content