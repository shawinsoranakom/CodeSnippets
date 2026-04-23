async def test_streaming_text_content():
    """Test that streamed text is coherent and complete."""
    text_events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-session-content",
        message="count to 3",
        is_user_message=True,
        user_id="test-user",
    ):
        if isinstance(event, StreamTextDelta):
            text_events.append(event)

    # Verify text deltas
    assert len(text_events) > 0, "Should have text deltas"

    # Reconstruct full text
    full_text = "".join(e.delta for e in text_events)
    assert len(full_text) > 0, "Text should not be empty"
    assert (
        "1" in full_text or "counted" in full_text.lower()
    ), "Text should contain count"

    # Verify all deltas have IDs
    for text_event in text_events:
        assert text_event.id, "Text delta must have ID"
        assert text_event.delta, "Text delta must have content"

    print(f"✅ Text content: '{full_text}' ({len(text_events)} deltas)")