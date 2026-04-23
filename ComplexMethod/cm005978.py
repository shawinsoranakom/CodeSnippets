async def test_agent_streaming_no_text_accumulation():
    """Test that agent streaming sends individual token events without accumulating text."""
    sent_messages = []
    token_events = []

    async def mock_send_message(message):
        # Capture each message sent for verification
        sent_messages.append(
            {"text": message.text, "state": message.properties.state, "id": getattr(message, "id", None)}
        )
        return message

    # Mock token callback to capture token events
    def mock_token_callback(data):
        # Capture token events
        token_events.append(data)

    event_manager = mock_token_callback

    agent_message = Message(
        sender=MESSAGE_SENDER_AI,
        sender_name="Agent",
        properties={"icon": "Bot", "state": "partial"},
        content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
        session_id="test_session_id",
    )
    # Add an ID to the message (normally set when persisted to DB)
    agent_message.data["id"] = "test-message-id"

    # Simulate streaming events with individual chunks
    events = [
        {
            "event": "on_chain_stream",
            "data": {"chunk": AIMessageChunk(content="Hello")},
        },
        {
            "event": "on_chain_stream",
            "data": {"chunk": AIMessageChunk(content=" world")},
        },
        {
            "event": "on_chain_stream",
            "data": {"chunk": AIMessageChunk(content="!")},
        },
        {
            "event": "on_chain_end",
            "data": {"output": AgentFinish(return_values={"output": "Hello world!"}, log="complete")},
        },
    ]

    result = await process_agent_events(create_event_iterator(events), agent_message, mock_send_message, event_manager)

    # Verify individual token events were sent (not accumulated)
    assert len(token_events) == 3, f"Expected 3 token events, got {len(token_events)}"

    # Each token event should contain only its chunk, not accumulated text
    assert token_events[0]["chunk"] == "Hello"
    assert token_events[1]["chunk"] == " world"
    assert token_events[2]["chunk"] == "!"

    # Verify all token events have the correct message ID
    for token_event in token_events:
        assert "id" in token_event
        assert token_event["id"] == "test-message-id"

    # Verify no token event contains accumulated text
    for token_event in token_events:
        assert "Hello world!" not in token_event["chunk"], f"Found accumulated text in chunk: {token_event['chunk']}"

    # Final result should have complete message with full text
    assert result.properties.state == "complete"
    assert result.text == "Hello world!"