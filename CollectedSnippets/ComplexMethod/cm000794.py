async def test_streaming_event_types():
    """Test that all expected event types are present."""
    event_types = set()

    async for event in stream_chat_completion_dummy(
        session_id="test-session-types",
        message="test",
        is_user_message=True,
        user_id="test-user",
    ):
        event_types.add(type(event).__name__)

    # Required event types for full AI SDK protocol
    assert "StreamStart" in event_types, "Missing StreamStart"
    assert "StreamStartStep" in event_types, "Missing StreamStartStep"
    assert "StreamTextStart" in event_types, "Missing StreamTextStart"
    assert "StreamTextDelta" in event_types, "Missing StreamTextDelta"
    assert "StreamTextEnd" in event_types, "Missing StreamTextEnd"
    assert "StreamFinishStep" in event_types, "Missing StreamFinishStep"
    assert "StreamFinish" in event_types, "Missing StreamFinish"

    print(f"✅ Event types: {sorted(event_types)}")