def test_parallel_tool_calls_with_limit_end_mode() -> None:
    """Test parallel tool calls with a limit of 1 in 'end' mode.

    When the model proposes 3 tool calls with a limit of 1:
    - The first call would be allowed (within limit)
    - The 2nd and 3rd calls exceed the limit and get blocked with error ToolMessages
    - Execution stops immediately (jump_to: end) so NO tools actually execute
    - An AI message explains why execution stopped
    """

    @tool
    def search(query: str) -> str:
        """Search for information."""
        return f"Results: {query}"

    # Model proposes 3 parallel search calls
    model = FakeToolCallingModel(
        tool_calls=[
            [
                ToolCall(name="search", args={"query": "q1"}, id="1"),
                ToolCall(name="search", args={"query": "q2"}, id="2"),
                ToolCall(name="search", args={"query": "q3"}, id="3"),
            ],
            [],
        ]
    )

    limiter = ToolCallLimitMiddleware(thread_limit=1, exit_behavior="end")
    agent = create_agent(
        model=model, tools=[search], middleware=[limiter], checkpointer=InMemorySaver()
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Test")]}, {"configurable": {"thread_id": "test"}}
    )
    messages = result["messages"]

    # Verify tool message counts
    # With "end" behavior, when we jump to end, NO tools execute (not even allowed ones)
    # We only get error ToolMessages for the 2 blocked calls
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    successful_tool_messages = [msg for msg in tool_messages if msg.status != "error"]
    error_tool_messages = [msg for msg in tool_messages if msg.status == "error"]

    assert len(successful_tool_messages) == 0, "No tools execute when we jump to end"
    assert len(error_tool_messages) == 2, "Should have 2 blocked tool messages (q2, q3)"

    # Verify error tool messages (sent to model - include "Do not" instruction)
    for error_msg in error_tool_messages:
        assert "Tool call limit exceeded" in error_msg.content
        assert "Do not" in error_msg.content

    # Verify AI message explaining why execution stopped
    # (displayed to user - includes thread/run details)
    ai_limit_messages = []
    for msg in messages:
        if not isinstance(msg, AIMessage):
            continue
        assert isinstance(msg.content, str)
        if "limit" in msg.content.lower() and not msg.tool_calls:
            ai_limit_messages.append(msg)
    assert len(ai_limit_messages) == 1, "Should have exactly one AI message explaining the limit"

    ai_msg_content = ai_limit_messages[0].content
    assert isinstance(ai_msg_content, str)
    assert "thread limit exceeded" in ai_msg_content.lower() or (
        "run limit exceeded" in ai_msg_content.lower()
    ), "AI message should include thread/run limit details for the user"