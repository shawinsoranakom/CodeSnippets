async def test_fatal_error_not_retryable():
    """Test __test_fatal_error__ yields StreamError without retryable code."""
    events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-fatal",
        message="__test_fatal_error__",
        is_user_message=True,
        user_id="test-user",
    ):
        events.append(event)

    assert isinstance(events[0], StreamStart)

    # Should have StreamError with sdk_error code (not transient)
    error_events = [e for e in events if isinstance(e, StreamError)]
    assert len(error_events) == 1
    assert error_events[0].code == "sdk_error"
    assert "transient" not in error_events[0].code

    # Should NOT have any text deltas (fatal errors fail immediately)
    text_events = [e for e in events if isinstance(e, StreamTextDelta)]
    assert len(text_events) == 0, "Fatal error should not stream any text"

    print("✅ Fatal error: immediate error, no partial text")