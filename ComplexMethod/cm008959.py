def test_parallel_tool_calls_with_limit_continue_mode() -> None:
    """Test parallel tool calls with a limit of 1 in 'continue' mode.

    When the model proposes 3 tool calls with a limit of 1:
    - The first call should execute successfully
    - The 2nd and 3rd calls should be blocked with error ToolMessages
    - Execution should continue (no jump_to)
    """

    @tool
    def search(query: str) -> str:
        """Search for information."""
        return f"Results: {query}"

    # Model proposes 3 parallel search calls in a single AIMessage
    model = FakeToolCallingModel(
        tool_calls=[
            [
                ToolCall(name="search", args={"query": "q1"}, id="1"),
                ToolCall(name="search", args={"query": "q2"}, id="2"),
                ToolCall(name="search", args={"query": "q3"}, id="3"),
            ],
            [],  # Model stops after seeing the errors
        ]
    )

    limiter = ToolCallLimitMiddleware(thread_limit=1, exit_behavior="continue")
    agent = create_agent(
        model=model, tools=[search], middleware=[limiter], checkpointer=InMemorySaver()
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Test")]}, {"configurable": {"thread_id": "test"}}
    )
    messages = result["messages"]

    # Verify tool message counts
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    successful_tool_messages = [msg for msg in tool_messages if msg.status != "error"]
    error_tool_messages = [msg for msg in tool_messages if msg.status == "error"]

    assert len(successful_tool_messages) == 1, "Should have 1 successful tool message (q1)"
    assert len(error_tool_messages) == 2, "Should have 2 blocked tool messages (q2, q3)"

    # Verify the successful call is q1
    assert "q1" in successful_tool_messages[0].content

    # Verify error messages explain the limit
    for error_msg in error_tool_messages:
        assert isinstance(error_msg.content, str)
        assert "limit" in error_msg.content.lower()

    # Verify execution continued (no early termination)
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    # Should have: initial AI message with 3 tool calls, then final AI message (no tool calls)
    assert len(ai_messages) >= 2