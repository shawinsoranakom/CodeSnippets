def test_summarization_middleware_helper_methods() -> None:
    """Test SummarizationMiddleware helper methods."""
    model = FakeToolCallingModel()
    middleware = SummarizationMiddleware(model=model, trigger=("tokens", 1000))

    # Test message ID assignment
    messages: list[AnyMessage] = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
    middleware._ensure_message_ids(messages)
    for msg in messages:
        assert msg.id is not None

    # Test message partitioning
    messages = [
        HumanMessage(content="1"),
        HumanMessage(content="2"),
        HumanMessage(content="3"),
        HumanMessage(content="4"),
        HumanMessage(content="5"),
    ]
    to_summarize, preserved = middleware._partition_messages(messages, 2)
    assert len(to_summarize) == 2
    assert len(preserved) == 3
    assert to_summarize == messages[:2]
    assert preserved == messages[2:]

    # Test summary message building
    summary = "This is a test summary"
    new_messages = middleware._build_new_messages(summary)
    assert len(new_messages) == 1
    assert isinstance(new_messages[0], HumanMessage)
    assert "Here is a summary of the conversation to date:" in new_messages[0].content
    assert summary in new_messages[0].content
    assert new_messages[0].additional_kwargs.get("lc_source") == "summarization"