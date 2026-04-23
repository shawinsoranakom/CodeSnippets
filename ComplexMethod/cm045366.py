def test_message_id_field() -> None:
    """Test that messages have unique ID fields automatically generated."""
    # Test BaseChatMessage subclass (TextMessage)
    message1 = TextMessage(source="test_agent", content="Hello, world!")
    message2 = TextMessage(source="test_agent", content="Hello, world!")

    # Check that IDs are present and unique
    assert hasattr(message1, "id")
    assert hasattr(message2, "id")
    assert message1.id != message2.id
    assert isinstance(message1.id, str)
    assert isinstance(message2.id, str)

    # Check that IDs are valid UUIDs
    try:
        uuid.UUID(message1.id)
        uuid.UUID(message2.id)
    except ValueError:
        pytest.fail("Generated IDs are not valid UUIDs")

    # Test BaseAgentEvent subclass (ModelClientStreamingChunkEvent)
    event1 = ModelClientStreamingChunkEvent(source="test_agent", content="chunk1")
    event2 = ModelClientStreamingChunkEvent(source="test_agent", content="chunk2")

    # Check that IDs are present and unique
    assert hasattr(event1, "id")
    assert hasattr(event2, "id")
    assert event1.id != event2.id
    assert isinstance(event1.id, str)
    assert isinstance(event2.id, str)

    # Check that IDs are valid UUIDs
    try:
        uuid.UUID(event1.id)
        uuid.UUID(event2.id)
    except ValueError:
        pytest.fail("Generated IDs are not valid UUIDs")