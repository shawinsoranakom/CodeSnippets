def test_run_limit_with_create_agent() -> None:
    """Test that run limits work correctly with create_agent."""
    # Create a model that will make 2 calls
    model = FakeToolCallingModel(
        tool_calls=[
            [{"name": "simple_tool", "args": {"input": "test"}, "id": "1"}],
            [],  # No tool calls on second call
        ]
    )

    # Set run limit to 1 (should be exceeded after 1 call)
    agent = create_agent(
        model=model,
        tools=[simple_tool],
        middleware=[ModelCallLimitMiddleware(run_limit=1)],
        checkpointer=InMemorySaver(),
    )

    # This should hit the run limit after the first model call
    result = agent.invoke(
        {"messages": [HumanMessage("Hello")]}, {"configurable": {"thread_id": "thread1"}}
    )

    assert "messages" in result
    # The agent should have made 1 model call then jumped to end with limit exceeded message
    # So we should have: Human + AI + Tool + Limit exceeded AI message
    assert len(result["messages"]) == 4  # Human + AI + Tool + Limit AI
    assert isinstance(result["messages"][0], HumanMessage)
    assert isinstance(result["messages"][1], AIMessage)
    assert isinstance(result["messages"][2], ToolMessage)
    assert isinstance(result["messages"][3], AIMessage)  # Limit exceeded message
    assert "run limit" in result["messages"][3].content