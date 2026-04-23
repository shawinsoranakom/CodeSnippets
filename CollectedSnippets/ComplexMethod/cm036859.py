def test_parser_state_to_response_output_commentary_channel() -> None:
    """Test parser_state_to_response_output with commentary
    channel and various recipients."""
    from unittest.mock import Mock

    # Test 1: functions.* recipient -> should return function tool call
    parser_func = Mock()
    parser_func.current_content = '{"arg": "value"}'
    parser_func.current_role = Role.ASSISTANT
    parser_func.current_channel = "commentary"
    parser_func.current_recipient = "functions.my_tool"

    func_items = parser_state_to_response_output(parser_func)

    assert len(func_items) == 1
    assert not isinstance(func_items[0], McpCall)
    assert func_items[0].type == "function_call"
    assert func_items[0].name == "my_tool"
    assert func_items[0].status == "in_progress"

    # Test 2: MCP tool (not builtin) -> should return MCP call
    parser_mcp = Mock()
    parser_mcp.current_content = '{"path": "/tmp"}'
    parser_mcp.current_role = Role.ASSISTANT
    parser_mcp.current_channel = "commentary"
    parser_mcp.current_recipient = "filesystem"

    mcp_items = parser_state_to_response_output(parser_mcp)

    assert len(mcp_items) == 1
    assert isinstance(mcp_items[0], McpCall)
    assert mcp_items[0].type == "mcp_call"
    assert mcp_items[0].name == "filesystem"
    assert mcp_items[0].server_label == "filesystem"
    assert mcp_items[0].status == "in_progress"

    # Test 3: Built-in tool (python)
    # should NOT return MCP call, returns reasoning (internal tool interaction)
    parser_builtin = Mock()
    parser_builtin.current_content = "print('hello')"
    parser_builtin.current_role = Role.ASSISTANT
    parser_builtin.current_channel = "commentary"
    parser_builtin.current_recipient = "python"

    builtin_items = parser_state_to_response_output(parser_builtin)

    # Built-in tools explicitly return reasoning
    assert len(builtin_items) == 1
    assert not isinstance(builtin_items[0], McpCall)
    assert builtin_items[0].type == "reasoning"

    # Test 4: No recipient (preamble) → should return message, not reasoning
    parser_preamble = Mock()
    parser_preamble.current_content = "I'll search for that information now."
    parser_preamble.current_role = Role.ASSISTANT
    parser_preamble.current_channel = "commentary"
    parser_preamble.current_recipient = None

    preamble_items = parser_state_to_response_output(parser_preamble)

    assert len(preamble_items) == 1
    assert isinstance(preamble_items[0], ResponseOutputMessage)
    assert preamble_items[0].type == "message"
    assert preamble_items[0].content[0].text == "I'll search for that information now."
    assert preamble_items[0].status == "incomplete"