async def test_handle_on_tool_start():
    """Test handle_on_tool_start event."""
    send_message = AsyncMock(side_effect=lambda message, skip_db_update=False: message)  # noqa: ARG005
    tool_blocks_map = {}
    agent_message = Message(
        sender=MESSAGE_SENDER_AI,
        sender_name="Agent",
        properties={"icon": "Bot", "state": "partial"},
        content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
    )
    event = {
        "event": "on_tool_start",
        "name": "test_tool",
        "run_id": "test_run",
        "data": {"input": {"query": "tool input"}},
        "start_time": 0,
    }

    updated_message, start_time = await handle_on_tool_start(event, agent_message, tool_blocks_map, send_message, 0.0)

    assert len(updated_message.content_blocks) == 1
    assert len(updated_message.content_blocks[0].contents) > 0
    tool_key = f"{event['name']}_{event['run_id']}"
    tool_content = updated_message.content_blocks[0].contents[-1]
    assert tool_content == tool_blocks_map.get(tool_key)
    assert isinstance(tool_content, ToolContent)
    assert tool_content.name == "test_tool"
    assert tool_content.tool_input == {"query": "tool input"}
    assert isinstance(tool_content.duration, int)
    assert isinstance(start_time, float)