def test_groq_translate_content_with_executed_tools() -> None:
    """Test groq content translation with executed tools (built-in tools)."""
    # Test with executed_tools in additional_kwargs (Groq built-in tools)
    message = AIMessage(
        content="",
        additional_kwargs={
            "executed_tools": [
                {
                    "type": "python",
                    "arguments": '{"code": "print(\\"hello\\")"}',
                    "output": "hello\\n",
                }
            ]
        },
    )
    blocks = translate_content(message)

    assert isinstance(blocks, list)
    # Should have server_tool_call and server_tool_result
    assert len(blocks) >= 2

    # Check for server_tool_call
    tool_call_blocks = [
        cast("types.ServerToolCall", b)
        for b in blocks
        if b.get("type") == "server_tool_call"
    ]
    assert len(tool_call_blocks) == 1
    assert tool_call_blocks[0]["name"] == "code_interpreter"
    assert "code" in tool_call_blocks[0]["args"]

    # Check for server_tool_result
    tool_result_blocks = [
        cast("types.ServerToolResult", b)
        for b in blocks
        if b.get("type") == "server_tool_result"
    ]
    assert len(tool_result_blocks) == 1
    assert tool_result_blocks[0]["output"] == "hello\\n"
    assert tool_result_blocks[0]["status"] == "success"