def test_datetime_serialization_in_messages() -> None:
    """Test that datetime objects in messages are properly serialized to JSON-compatible format.

    This test validates the fix for issue #6793 where datetime objects in message
    created_at fields caused JSON serialization errors when saving team state.
    """
    # Create a specific datetime for testing
    test_datetime = datetime(2023, 12, 25, 10, 30, 45, 123456, timezone.utc)

    # Test BaseChatMessage subclass with datetime
    chat_message = TextMessage(source="test_agent", content="Hello, world!", created_at=test_datetime)

    # Test that dump() returns JSON-serializable data
    chat_message_data = chat_message.dump()

    # Verify that the datetime is converted to a string in ISO format
    assert isinstance(chat_message_data["created_at"], str)
    # Pydantic JSON mode converts UTC timezone to 'Z' format instead of '+00:00'
    expected_iso = test_datetime.isoformat().replace("+00:00", "Z")
    assert chat_message_data["created_at"] == expected_iso

    # Verify that the dumped data is JSON serializable
    json_string = json.dumps(chat_message_data)
    assert isinstance(json_string, str)

    # Test round-trip serialization (dump -> load)
    restored_chat_message = TextMessage.load(chat_message_data)
    assert restored_chat_message.source == "test_agent"
    assert restored_chat_message.content == "Hello, world!"
    assert restored_chat_message.created_at == test_datetime

    # Test BaseAgentEvent subclass with datetime
    agent_event = ModelClientStreamingChunkEvent(source="test_agent", content="chunk", created_at=test_datetime)

    # Test that dump() returns JSON-serializable data
    agent_event_data = agent_event.dump()

    # Verify that the datetime is converted to a string in ISO format
    assert isinstance(agent_event_data["created_at"], str)
    assert agent_event_data["created_at"] == expected_iso

    # Verify that the dumped data is JSON serializable
    json_string = json.dumps(agent_event_data)
    assert isinstance(json_string, str)

    # Test round-trip serialization (dump -> load)
    restored_agent_event = ModelClientStreamingChunkEvent.load(agent_event_data)
    assert restored_agent_event.source == "test_agent"
    assert restored_agent_event.content == "chunk"
    assert restored_agent_event.created_at == test_datetime

    # Test with auto-generated datetime (default created_at)
    auto_message = TextMessage(source="test_agent", content="Auto datetime test")
    auto_message_data = auto_message.dump()

    # Verify datetime is serialized as string
    assert isinstance(auto_message_data["created_at"], str)

    # Verify JSON serialization works without errors
    json.dumps(auto_message_data)

    # Test round-trip with auto-generated datetime
    restored_auto_message = TextMessage.load(auto_message_data)
    assert restored_auto_message.created_at == auto_message.created_at