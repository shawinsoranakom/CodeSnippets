def test_message_serialization_with_id() -> None:
    """Test that messages with IDs serialize and deserialize correctly."""
    # Create a message with auto-generated ID
    original_message = TextMessage(source="test_agent", content="Hello, world!")
    original_id = original_message.id

    # Serialize to dict
    message_data = original_message.model_dump()
    assert "id" in message_data
    assert message_data["id"] == original_id

    # Deserialize from dict
    restored_message = TextMessage.model_validate(message_data)
    assert restored_message.id == original_id
    assert restored_message.source == "test_agent"
    assert restored_message.content == "Hello, world!"

    # Test with streaming chunk event
    original_chunk = ModelClientStreamingChunkEvent(
        source="test_agent", content="chunk", full_message_id="full-msg-123"
    )
    original_chunk_id = original_chunk.id

    # Serialize to dict
    chunk_data = original_chunk.model_dump()
    assert "id" in chunk_data
    assert "full_message_id" in chunk_data
    assert chunk_data["id"] == original_chunk_id
    assert chunk_data["full_message_id"] == "full-msg-123"

    # Deserialize from dict
    restored_chunk = ModelClientStreamingChunkEvent.model_validate(chunk_data)
    assert restored_chunk.id == original_chunk_id
    assert restored_chunk.full_message_id == "full-msg-123"
    assert restored_chunk.content == "chunk"