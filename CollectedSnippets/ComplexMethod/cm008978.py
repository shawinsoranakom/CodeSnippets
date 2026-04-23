def test_summarization_middleware_full_workflow() -> None:
    """Test SummarizationMiddleware complete summarization workflow."""
    with pytest.warns(DeprecationWarning, match="messages_to_keep is deprecated"):
        # keep test for functionality
        middleware = SummarizationMiddleware(
            model=MockChatModel(), max_tokens_before_summary=1000, messages_to_keep=2
        )

    # Mock high token count to trigger summarization
    def mock_token_counter(_: Iterable[MessageLikeRepresentation]) -> int:
        return 1500  # Above threshold

    middleware.token_counter = mock_token_counter

    messages: list[AnyMessage] = [
        HumanMessage(content="1"),
        HumanMessage(content="2"),
        HumanMessage(content="3"),
        HumanMessage(content="4"),
        HumanMessage(content="5"),
    ]

    state = AgentState[Any](messages=messages)
    result = middleware.before_model(state, Runtime())

    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0

    # Should have RemoveMessage for cleanup
    assert isinstance(result["messages"][0], RemoveMessage)
    assert result["messages"][0].id == REMOVE_ALL_MESSAGES

    # Should have summary message
    summary_message = None
    for msg in result["messages"]:
        if isinstance(msg, HumanMessage) and "summary of the conversation" in msg.content:
            summary_message = msg
            break

    assert summary_message is not None
    assert "Generated summary" in summary_message.content