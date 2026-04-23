def test_streaming_cache_token_reporting() -> None:
    """Test that cache tokens are properly reported in streaming events."""
    from unittest.mock import MagicMock

    from anthropic.types import MessageDeltaUsage

    # Create a mock message_start event
    mock_message = MagicMock()
    mock_message.model = MODEL_NAME
    mock_message.usage.input_tokens = 100
    mock_message.usage.output_tokens = 0
    mock_message.usage.cache_read_input_tokens = 25
    mock_message.usage.cache_creation_input_tokens = 10

    message_start_event = MagicMock()
    message_start_event.type = "message_start"
    message_start_event.message = mock_message

    # Create a mock message_delta event with complete usage info
    mock_delta_usage = MessageDeltaUsage(
        output_tokens=50,
        input_tokens=100,
        cache_read_input_tokens=25,
        cache_creation_input_tokens=10,
    )

    mock_delta = MagicMock()
    mock_delta.stop_reason = "end_turn"
    mock_delta.stop_sequence = None

    message_delta_event = MagicMock()
    message_delta_event.type = "message_delta"
    message_delta_event.usage = mock_delta_usage
    message_delta_event.delta = mock_delta

    llm = ChatAnthropic(model=MODEL_NAME)  # type: ignore[call-arg]

    # Test message_start event
    start_chunk, _ = llm._make_message_chunk_from_anthropic_event(
        message_start_event,
        stream_usage=True,
        coerce_content_to_string=True,
        block_start_event=None,
    )

    # Test message_delta event - should contain complete usage metadata (w/ cache)
    delta_chunk, _ = llm._make_message_chunk_from_anthropic_event(
        message_delta_event,
        stream_usage=True,
        coerce_content_to_string=True,
        block_start_event=None,
    )

    # Verify message_delta has complete usage_metadata including cache tokens
    assert start_chunk is not None, "message_start should produce a chunk"
    assert getattr(start_chunk, "usage_metadata", None) is None, (
        "message_start should not have usage_metadata"
    )
    assert delta_chunk is not None, "message_delta should produce a chunk"
    assert delta_chunk.usage_metadata is not None, (
        "message_delta should have usage_metadata"
    )
    assert "input_token_details" in delta_chunk.usage_metadata
    input_details = delta_chunk.usage_metadata["input_token_details"]
    assert input_details.get("cache_read") == 25
    assert input_details.get("cache_creation") == 10

    # Verify totals are correct: 100 base + 25 cache_read + 10 cache_creation = 135
    assert delta_chunk.usage_metadata["input_tokens"] == 135
    assert delta_chunk.usage_metadata["output_tokens"] == 50
    assert delta_chunk.usage_metadata["total_tokens"] == 185