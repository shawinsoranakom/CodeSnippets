async def test_tool_start_event():
    """Test handling of on_tool_start event."""
    call_count = [0]

    def update_message(message, skip_db_update=False):  # noqa: ARG001, FBT002
        call_count[0] += 1
        if call_count[0] == 1:
            # Simulate production: add ID on first call (when persisting to DB)
            message.data["id"] = "test-message-id"
        # Return a copy of the message to simulate real behavior
        return Message(**message.model_dump())

    send_message = AsyncMock(side_effect=update_message)

    events = [
        {
            "event": "on_tool_start",
            "name": "test_tool",
            "run_id": "test_run",
            "data": {"input": {"query": "tool input"}},
            "start_time": 0,
        }
    ]
    agent_message = Message(
        sender=MESSAGE_SENDER_AI,
        sender_name="Agent",
        properties={"icon": "Bot", "state": "partial"},
        content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
        session_id="test_session_id",
    )
    result = await process_agent_events(create_event_iterator(events), agent_message, send_message)

    assert result.properties.icon == "Bot"
    assert len(result.content_blocks) == 1
    assert result.content_blocks[0].title == "Agent Steps"
    assert len(result.content_blocks[0].contents) > 0
    tool_content = result.content_blocks[0].contents[-1]
    assert isinstance(tool_content, ToolContent)
    assert tool_content.name == "test_tool"
    assert tool_content.tool_input == {"query": "tool input"}, tool_content