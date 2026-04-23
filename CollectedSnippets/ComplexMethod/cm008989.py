def test_thread_limit_with_create_agent() -> None:
    """Test that thread limits work correctly with create_agent."""
    model = FakeToolCallingModel()

    # Set thread limit to 1 (should be exceeded after 1 call)
    agent = create_agent(
        model=model,
        tools=[simple_tool],
        middleware=[ModelCallLimitMiddleware(thread_limit=1)],
        checkpointer=InMemorySaver(),
    )

    # First invocation should work - 1 model call, within thread limit
    result = agent.invoke(
        {"messages": [HumanMessage("Hello")]}, {"configurable": {"thread_id": "thread1"}}
    )

    # Should complete successfully with 1 model call
    assert "messages" in result
    assert len(result["messages"]) == 2  # Human + AI messages

    # Second invocation in same thread should hit thread limit
    # The agent should jump to end after detecting the limit
    result2 = agent.invoke(
        {"messages": [HumanMessage("Hello again")]}, {"configurable": {"thread_id": "thread1"}}
    )

    assert "messages" in result2
    # The agent should have detected the limit and jumped to end with a limit exceeded message
    # So we should have: previous messages + new human message + limit exceeded AI message
    assert len(result2["messages"]) == 4  # Previous Human + AI + New Human + Limit AI
    assert isinstance(result2["messages"][0], HumanMessage)  # First human
    assert isinstance(result2["messages"][1], AIMessage)  # First AI response
    assert isinstance(result2["messages"][2], HumanMessage)  # Second human
    assert isinstance(result2["messages"][3], AIMessage)  # Limit exceeded message
    assert "thread limit" in result2["messages"][3].content