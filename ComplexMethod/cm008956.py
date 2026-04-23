def test_exit_behavior_continue() -> None:
    """Test that exit_behavior='continue' blocks only the exceeded tool, not others.

    Verifies that when a specific tool hits its limit, it gets blocked with error messages
    while other tools continue to execute normally.
    """

    @tool
    def search(query: str) -> str:
        """Search for information."""
        return f"Search: {query}"

    @tool
    def calculator(expression: str) -> str:
        """Calculate an expression."""
        return f"Calc: {expression}"

    model = FakeToolCallingModel(
        tool_calls=[
            [
                ToolCall(name="search", args={"query": "q1"}, id="1"),
                ToolCall(name="calculator", args={"expression": "1+1"}, id="2"),
            ],
            [
                ToolCall(name="search", args={"query": "q2"}, id="3"),
                ToolCall(name="calculator", args={"expression": "2+2"}, id="4"),
            ],
            [
                ToolCall(name="search", args={"query": "q3"}, id="5"),  # Should be blocked
                ToolCall(name="calculator", args={"expression": "3+3"}, id="6"),  # Should work
            ],
            [],
        ]
    )

    # Limit search to 2 calls, but allow other tools to continue
    search_limiter = ToolCallLimitMiddleware(
        tool_name="search", thread_limit=2, exit_behavior="continue"
    )

    agent = create_agent(
        model=model,
        tools=[search, calculator],
        middleware=[search_limiter],
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Question")]},
        {"configurable": {"thread_id": "test_thread"}},
    )

    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]

    # Verify search has 2 successful + 1 blocked, calculator has all 3 successful
    successful_search_msgs = [msg for msg in tool_messages if "Search:" in msg.content]
    blocked_search_msgs = []
    for msg in tool_messages:
        assert isinstance(msg.content, str)
        if "limit" in msg.content.lower() and "search" in msg.content.lower():
            blocked_search_msgs.append(msg)
    successful_calc_msgs = [msg for msg in tool_messages if "Calc:" in msg.content]

    assert len(successful_search_msgs) == 2, "Should have 2 successful search calls"
    assert len(blocked_search_msgs) == 1, "Should have 1 blocked search call with limit error"
    assert len(successful_calc_msgs) == 3, "All calculator calls should succeed"