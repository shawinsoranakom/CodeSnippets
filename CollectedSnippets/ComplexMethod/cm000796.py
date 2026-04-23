async def test_event_ordering():
    """Test that events arrive in correct order."""
    events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-ordering",
        message="Test",
        is_user_message=True,
        user_id="test-user",
    ):
        events.append(event)

    # Find event indices
    start_idx = next(
        (i for i, e in enumerate(events) if isinstance(e, StreamStart)), None
    )
    text_indices = [i for i, e in enumerate(events) if isinstance(e, StreamTextDelta)]

    # Verify ordering
    assert start_idx is not None, "Should have StreamStart"
    assert start_idx == 0, "StreamStart should be first"

    if text_indices:
        assert all(
            start_idx < i for i in text_indices
        ), "Text deltas should be after start"

    print(f"✅ Event ordering: start({start_idx}) < text deltas")