def test_builtin_tools_computer_use() -> None:
    """Test computer use tool integration.

    Beta header should be automatically appended based on tool type.

    This test only verifies tool call generation.
    """
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore[call-arg]
    )
    tool = {
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768,
        "display_number": 1,
    }
    llm_with_tools = llm.bind_tools([tool])
    response = llm_with_tools.invoke(
        "Can you take a screenshot to see what's on the screen?",
    )
    assert isinstance(response, AIMessage)
    assert response.tool_calls

    content_blocks = response.content_blocks
    assert len(content_blocks) >= 2
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[0]["text"]

    # Check that we have a tool_call for computer use
    tool_call_blocks = [b for b in content_blocks if b["type"] == "tool_call"]
    assert len(tool_call_blocks) >= 1
    assert tool_call_blocks[0]["name"] == "computer"

    # Verify tool call has expected action (screenshot in this case)
    tool_call = response.tool_calls[0]
    assert tool_call["name"] == "computer"
    assert "action" in tool_call["args"]
    assert tool_call["args"]["action"] == "screenshot"