async def test_dummy_streaming_basic_flow():
    """Test that dummy streaming produces correct event sequence."""
    events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-session-basic",
        message="Hello",
        is_user_message=True,
        user_id="test-user",
    ):
        events.append(event)

    # Verify we got events
    assert len(events) > 0, "Should receive events"

    # Verify StreamStart
    start_events = [e for e in events if isinstance(e, StreamStart)]
    assert len(start_events) == 1
    assert start_events[0].messageId
    assert start_events[0].sessionId

    # Verify StreamTextDelta events
    text_events = [e for e in events if isinstance(e, StreamTextDelta)]
    assert len(text_events) > 0
    full_text = "".join(e.delta for e in text_events)
    assert len(full_text) > 0

    # Verify order: start before text
    start_idx = events.index(start_events[0])
    first_text_idx = events.index(text_events[0]) if text_events else -1
    if first_text_idx >= 0:
        assert start_idx < first_text_idx

    print(f"✅ Basic flow: {len(events)} events, {len(text_events)} text deltas")