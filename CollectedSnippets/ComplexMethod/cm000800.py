async def test_text_delta_consistency():
    """Test that text deltas have consistent IDs and build coherent text."""
    text_events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-consistency",
        message="Test consistency",
        is_user_message=True,
        user_id="test-user",
    ):
        if isinstance(event, StreamTextDelta):
            text_events.append(event)

    # Verify all text deltas have IDs
    assert all(e.id for e in text_events), "All text deltas must have IDs"

    # Verify all deltas have the same ID (same text block)
    if text_events:
        first_id = text_events[0].id
        assert all(
            e.id == first_id for e in text_events
        ), "All text deltas should share the same block ID"

    # Verify deltas build coherent text
    full_text = "".join(e.delta for e in text_events)
    assert len(full_text) > 0, "Deltas should build non-empty text"
    assert (
        full_text == full_text.strip()
    ), "Text should not have leading/trailing whitespace artifacts"

    print(
        f"✅ Consistency: {len(text_events)} deltas with ID '{text_events[0].id if text_events else 'N/A'}', text: '{full_text}'"
    )