def test_run_limit_with_multiple_human_messages() -> None:
    """Test that run limits reset between invocations.

    Verifies that when using run_limit, the count resets for each new user message,
    allowing execution to continue across multiple invocations in the same thread.
    """

    @tool
    def search(query: str) -> str:
        """Search for information."""
        return f"Results for {query}"

    model = FakeToolCallingModel(
        tool_calls=[
            [ToolCall(name="search", args={"query": "test1"}, id="1")],
            [ToolCall(name="search", args={"query": "test2"}, id="2")],
            [],
        ]
    )

    middleware = ToolCallLimitMiddleware(run_limit=1, exit_behavior="end")
    agent = create_agent(
        model=model, tools=[search], middleware=[middleware], checkpointer=InMemorySaver()
    )

    # First invocation: test1 executes successfully, test2 exceeds limit
    result1 = agent.invoke(
        {"messages": [HumanMessage("Question 1")]},
        {"configurable": {"thread_id": "test_thread"}},
    )
    tool_messages = [msg for msg in result1["messages"] if isinstance(msg, ToolMessage)]
    successful_tool_msgs = [msg for msg in tool_messages if msg.status != "error"]
    error_tool_msgs = [msg for msg in tool_messages if msg.status == "error"]
    ai_limit_msgs = []
    for msg in result1["messages"]:
        if not isinstance(msg, AIMessage):
            continue
        assert isinstance(msg.content, str)
        if "limit" in msg.content.lower() and not msg.tool_calls:
            ai_limit_msgs.append(msg)

    assert len(successful_tool_msgs) == 1, "Should have 1 successful tool execution (test1)"
    assert len(error_tool_msgs) == 1, "Should have 1 artificial error ToolMessage (test2)"
    assert len(ai_limit_msgs) == 1, "Should have AI limit message after test2 proposed"

    # Second invocation: run limit should reset, allowing continued execution
    result2 = agent.invoke(
        {"messages": [HumanMessage("Question 2")]},
        {"configurable": {"thread_id": "test_thread"}},
    )

    assert len(result2["messages"]) > len(result1["messages"]), (
        "Second invocation should add new messages, proving run limit reset"
    )