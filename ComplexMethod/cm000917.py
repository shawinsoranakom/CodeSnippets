def test_tool_use_emits_input_start_and_available():
    """Tool names arrive with MCP prefix and should be stripped for the frontend."""
    adapter = _adapter()
    msg = AssistantMessage(
        content=[
            ToolUseBlock(
                id="tool-1",
                name=f"{MCP_TOOL_PREFIX}find_agent",
                input={"q": "x"},
            )
        ],
        model="test",
    )
    results = adapter.convert_message(msg)
    assert len(results) == 3
    assert isinstance(results[0], StreamStartStep)
    assert isinstance(results[1], StreamToolInputStart)
    assert results[1].toolCallId == "tool-1"
    assert results[1].toolName == "find_agent"  # prefix stripped
    assert isinstance(results[2], StreamToolInputAvailable)
    assert results[2].toolName == "find_agent"  # prefix stripped
    assert results[2].input == {"q": "x"}