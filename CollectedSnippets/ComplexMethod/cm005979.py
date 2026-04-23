async def test_agent_streaming_preserves_message_id():
    """Test that agent streaming preserves message ID throughout event processing."""
    token_events = []
    call_count = [0]

    async def mock_send_message(message):
        # Simulate persisting the message and returning with ID on first call
        call_count[0] += 1
        if call_count[0] == 1:
            # First call - add the ID
            message.data["id"] = "test-persisted-id"
        return message

    def mock_token_callback(data):
        token_events.append(data)

    event_manager = mock_token_callback

    # Create message WITHOUT an ID initially
    agent_message = Message(
        sender=MESSAGE_SENDER_AI,
        sender_name="Agent",
        properties={"icon": "Bot", "state": "partial"},
        content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
        session_id="test_session_id",
    )

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
            "event": "on_chain_end",
            "data": {"output": AgentFinish(return_values={"output": "Hello world"}, log="complete")},
        },
    ]

    result = await process_agent_events(create_event_iterator(events), agent_message, mock_send_message, event_manager)

    # Verify token events were sent with the persisted ID
    assert len(token_events) == 2, f"Expected 2 token events, got {len(token_events)}"
    assert token_events[0]["chunk"] == "Hello"
    assert token_events[0]["id"] == "test-persisted-id"
    assert token_events[1]["chunk"] == " world"
    assert token_events[1]["id"] == "test-persisted-id"
    assert result.properties.state == "complete"
    assert result.text == "Hello world"