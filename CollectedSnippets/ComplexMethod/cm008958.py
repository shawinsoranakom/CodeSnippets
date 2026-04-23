def test_end_behavior_creates_artificial_messages() -> None:
    """Test that 'end' behavior creates an AI message explaining why execution stopped.

    Verifies that when limit is exceeded with exit_behavior='end', the middleware:
    1. Injects an artificial error ToolMessage for the blocked tool call
    2. Adds an AI message explaining the limit to the user
    3. Jumps to end, stopping execution
    """

    @tool
    def search(query: str) -> str:
        """Search for information."""
        return f"Results: {query}"

    model = FakeToolCallingModel(
        tool_calls=[
            [ToolCall(name="search", args={"query": "q1"}, id="1")],
            [ToolCall(name="search", args={"query": "q2"}, id="2")],
            [ToolCall(name="search", args={"query": "q3"}, id="3")],  # Exceeds limit
            [],
        ]
    )

    limiter = ToolCallLimitMiddleware(thread_limit=2, exit_behavior="end")
    agent = create_agent(
        model=model, tools=[search], middleware=[limiter], checkpointer=InMemorySaver()
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Test")]}, {"configurable": {"thread_id": "test"}}
    )

    # Verify AI message explaining the limit (displayed to user - includes thread/run details)
    ai_limit_messages = []
    for msg in result["messages"]:
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

    # Verify tool message counts
    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    successful_tool_msgs = [msg for msg in tool_messages if msg.status != "error"]
    error_tool_msgs = [msg for msg in tool_messages if msg.status == "error"]

    assert len(successful_tool_msgs) == 2, "Should have 2 successful tool messages (q1, q2)"
    assert len(error_tool_msgs) == 1, "Should have 1 artificial error tool message (q3)"

    # Verify the error tool message (sent to model - no thread/run details, includes instruction)
    error_msg_content = error_tool_msgs[0].content
    assert "Tool call limit exceeded" in error_msg_content
    assert "Do not" in error_msg_content, (
        "Tool message should instruct model not to call tool again"
    )