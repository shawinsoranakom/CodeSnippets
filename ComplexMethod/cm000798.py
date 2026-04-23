async def test_transient_error_shows_retryable():
    """Test __test_transient_error__ yields partial text then retryable StreamError."""
    events = []

    async for event in stream_chat_completion_dummy(
        session_id="test-transient",
        message="please fail __test_transient_error__",
        is_user_message=True,
        user_id="test-user",
    ):
        events.append(event)

    # Should start with StreamStart
    assert isinstance(events[0], StreamStart)

    # Should have some partial text before the error
    text_events = [e for e in events if isinstance(e, StreamTextDelta)]
    assert len(text_events) > 0, "Should stream partial text before error"

    # Should end with StreamError
    error_events = [e for e in events if isinstance(e, StreamError)]
    assert len(error_events) == 1, "Should have exactly one StreamError"
    assert error_events[0].code == "transient_api_error"
    assert "connection interrupted" in error_events[0].errorText.lower()

    print(f"✅ Transient error: {len(text_events)} partial deltas + retryable error")