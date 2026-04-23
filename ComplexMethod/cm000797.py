async def test_stream_completeness():
    """Test that stream includes all required event types."""
    events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-completeness",
        message="Complete stream test",
        is_user_message=True,
        user_id="test-user",
    ):
        events.append(event)

    # Check for all required event types
    assert any(isinstance(e, StreamStart) for e in events), "Missing StreamStart"
    assert any(
        isinstance(e, StreamStartStep) for e in events
    ), "Missing StreamStartStep"
    assert any(
        isinstance(e, StreamTextStart) for e in events
    ), "Missing StreamTextStart"
    assert any(
        isinstance(e, StreamTextDelta) for e in events
    ), "Missing StreamTextDelta"
    assert any(isinstance(e, StreamTextEnd) for e in events), "Missing StreamTextEnd"
    assert any(
        isinstance(e, StreamFinishStep) for e in events
    ), "Missing StreamFinishStep"
    assert any(isinstance(e, StreamFinish) for e in events), "Missing StreamFinish"

    # Verify exactly one start
    start_count = sum(1 for e in events if isinstance(e, StreamStart))
    assert start_count == 1, f"Should have exactly 1 StreamStart, got {start_count}"

    print(f"✅ Completeness: {len(events)} events, full protocol sequence")