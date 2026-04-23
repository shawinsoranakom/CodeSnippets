def test_summarization_middleware_keep_messages() -> None:
    """Test SummarizationMiddleware with keep parameter specifying messages."""
    # Test that summarization is triggered when message count reaches threshold
    middleware = SummarizationMiddleware(
        model=MockChatModel(), trigger=("messages", 5), keep=("messages", 2)
    )

    # Below threshold - no summarization
    messages_below: list[AnyMessage] = [
        HumanMessage(content="1"),
        HumanMessage(content="2"),
        HumanMessage(content="3"),
        HumanMessage(content="4"),
    ]
    state_below = AgentState[Any](messages=messages_below)
    result = middleware.before_model(state_below, Runtime())
    assert result is None

    # At threshold - should trigger summarization
    messages_at_threshold: list[AnyMessage] = [
        HumanMessage(content="1"),
        HumanMessage(content="2"),
        HumanMessage(content="3"),
        HumanMessage(content="4"),
        HumanMessage(content="5"),
    ]
    state_at = AgentState[Any](messages=messages_at_threshold)
    result = middleware.before_model(state_at, Runtime())
    assert result is not None
    assert "messages" in result
    expected_types = ["remove", "human", "human", "human"]
    actual_types = [message.type for message in result["messages"]]
    assert actual_types == expected_types
    assert [message.content for message in result["messages"][2:]] == ["4", "5"]

    # Above threshold - should also trigger summarization
    messages_above: list[AnyMessage] = [*messages_at_threshold, HumanMessage(content="6")]
    state_above = AgentState[Any](messages=messages_above)
    result = middleware.before_model(state_above, Runtime())
    assert result is not None
    assert "messages" in result
    expected_types = ["remove", "human", "human", "human"]
    actual_types = [message.type for message in result["messages"]]
    assert actual_types == expected_types
    assert [message.content for message in result["messages"][2:]] == ["5", "6"]

    # Test with both parameters disabled
    middleware_disabled = SummarizationMiddleware(model=MockChatModel(), trigger=None)
    result = middleware_disabled.before_model(state_above, Runtime())
    assert result is None