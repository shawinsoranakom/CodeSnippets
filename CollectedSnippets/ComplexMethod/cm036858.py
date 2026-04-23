def test_parse_mcp_call_basic() -> None:
    """Test that MCP calls are parsed with correct type and server_label."""
    message = Message.from_role_and_content(Role.ASSISTANT, '{"path": "/tmp"}')
    message = message.with_recipient("filesystem")
    message = message.with_channel("commentary")

    output_items = harmony_to_response_output(message)

    assert len(output_items) == 1
    assert isinstance(output_items[0], McpCall)
    assert output_items[0].type == "mcp_call"
    assert output_items[0].name == "filesystem"
    assert output_items[0].server_label == "filesystem"
    assert output_items[0].arguments == '{"path": "/tmp"}'
    assert output_items[0].status == "completed"