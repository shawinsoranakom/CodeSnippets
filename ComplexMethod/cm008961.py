def test_parallel_mixed_tool_calls_with_specific_tool_limit() -> None:
    """Test parallel calls to different tools when limiting a specific tool.

    When limiting 'search' to 1 call, and model proposes 3 search + 2 calculator calls:
    - First search call should execute
    - Other 2 search calls should be blocked
    - All calculator calls should execute (not limited)
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
                ToolCall(name="search", args={"query": "q2"}, id="3"),
                ToolCall(name="calculator", args={"expression": "2+2"}, id="4"),
                ToolCall(name="search", args={"query": "q3"}, id="5"),
            ],
            [],
        ]
    )

    search_limiter = ToolCallLimitMiddleware(
        tool_name="search", thread_limit=1, exit_behavior="continue"
    )
    agent = create_agent(
        model=model,
        tools=[search, calculator],
        middleware=[search_limiter],
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Test")]}, {"configurable": {"thread_id": "test"}}
    )
    messages = result["messages"]

    search_success = []
    search_blocked = []
    calc_success = []
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        assert isinstance(m.content, str)
        if "Search:" in m.content:
            search_success.append(m)
        if "limit" in m.content.lower() and "search" in m.content.lower():
            search_blocked.append(m)
        if "Calc:" in m.content:
            calc_success.append(m)

    assert len(search_success) == 1, "Should have 1 successful search call"
    assert len(search_blocked) == 2, "Should have 2 blocked search calls"
    assert len(calc_success) == 2, "All calculator calls should succeed (not limited)"