def test_tool_result_emits_output_and_finish_step():
    adapter = _adapter()
    # First register the tool call (opens step) — SDK sends prefixed name
    tool_msg = AssistantMessage(
        content=[ToolUseBlock(id="t1", name=f"{MCP_TOOL_PREFIX}find_agent", input={})],
        model="test",
    )
    adapter.convert_message(tool_msg)

    # Now send tool result
    result_msg = UserMessage(
        content=[ToolResultBlock(tool_use_id="t1", content="found 3 agents")]
    )
    results = adapter.convert_message(result_msg)
    assert len(results) == 2
    assert isinstance(results[0], StreamToolOutputAvailable)
    assert results[0].toolCallId == "t1"
    assert results[0].toolName == "find_agent"  # prefix stripped
    assert results[0].output == "found 3 agents"
    assert results[0].success is True
    assert isinstance(results[1], StreamFinishStep)