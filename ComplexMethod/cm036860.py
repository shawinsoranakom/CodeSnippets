def test_parser_state_to_response_output_analysis_channel() -> None:
    """Test parser_state_to_response_output with analysis
    channel and various recipients."""
    from unittest.mock import Mock

    # Test 1: functions.* recipient -> should return function tool call
    parser_func = Mock()
    parser_func.current_content = '{"arg": "value"}'
    parser_func.current_role = Role.ASSISTANT
    parser_func.current_channel = "analysis"
    parser_func.current_recipient = "functions.my_tool"

    func_items = parser_state_to_response_output(parser_func)

    assert len(func_items) == 1
    assert not isinstance(func_items[0], McpCall)
    assert func_items[0].type == "function_call"
    assert func_items[0].name == "my_tool"
    assert func_items[0].status == "in_progress"

    # Test 2: MCP tool (not builtin) -> should return MCP call
    parser_mcp = Mock()
    parser_mcp.current_content = '{"query": "test"}'
    parser_mcp.current_role = Role.ASSISTANT
    parser_mcp.current_channel = "analysis"
    parser_mcp.current_recipient = "database"

    mcp_items = parser_state_to_response_output(parser_mcp)

    assert len(mcp_items) == 1
    assert isinstance(mcp_items[0], McpCall)
    assert mcp_items[0].type == "mcp_call"
    assert mcp_items[0].name == "database"
    assert mcp_items[0].server_label == "database"
    assert mcp_items[0].status == "in_progress"

    # Test 3: Built-in tool (container)
    # should NOT return MCP call, falls through to reasoning
    parser_builtin = Mock()
    parser_builtin.current_content = "docker run"
    parser_builtin.current_role = Role.ASSISTANT
    parser_builtin.current_channel = "analysis"
    parser_builtin.current_recipient = "container"

    builtin_items = parser_state_to_response_output(parser_builtin)

    # Should fall through to reasoning logic
    assert len(builtin_items) == 1
    assert not isinstance(builtin_items[0], McpCall)
    assert builtin_items[0].type == "reasoning"