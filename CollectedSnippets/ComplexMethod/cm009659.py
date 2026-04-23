def test_typed_init() -> None:
    ai_message = AIMessage(content_blocks=[{"type": "text", "text": "Hello"}])
    assert ai_message.content == [{"type": "text", "text": "Hello"}]
    assert ai_message.content_blocks == ai_message.content

    human_message = HumanMessage(content_blocks=[{"type": "text", "text": "Hello"}])
    assert human_message.content == [{"type": "text", "text": "Hello"}]
    assert human_message.content_blocks == human_message.content

    system_message = SystemMessage(content_blocks=[{"type": "text", "text": "Hello"}])
    assert system_message.content == [{"type": "text", "text": "Hello"}]
    assert system_message.content_blocks == system_message.content

    tool_message = ToolMessage(
        content_blocks=[{"type": "text", "text": "Hello"}],
        tool_call_id="abc123",
    )
    assert tool_message.content == [{"type": "text", "text": "Hello"}]
    assert tool_message.content_blocks == tool_message.content

    for message_class in [AIMessage, HumanMessage, SystemMessage]:
        message = message_class("Hello")
        assert message.content == "Hello"
        assert message.content_blocks == [{"type": "text", "text": "Hello"}]

        message = message_class(content="Hello")
        assert message.content == "Hello"
        assert message.content_blocks == [{"type": "text", "text": "Hello"}]

    # Test we get type errors for malformed blocks (type checker will complain if
    # below type-ignores are unused).
    _ = AIMessage(content_blocks=[{"type": "text", "bad": "Hello"}])  # type: ignore[list-item]
    _ = HumanMessage(content_blocks=[{"type": "text", "bad": "Hello"}])  # type: ignore[list-item]
    _ = SystemMessage(content_blocks=[{"type": "text", "bad": "Hello"}])  # type: ignore[list-item]
    _ = ToolMessage(
        content_blocks=[{"type": "text", "bad": "Hello"}],  # type: ignore[list-item]
        tool_call_id="abc123",
    )