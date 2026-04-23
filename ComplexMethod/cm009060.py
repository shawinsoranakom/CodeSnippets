def test_no_duplicate_tool_calls_when_multiple_tools() -> None:
    """
    Tests whether the conversion of an AIMessage with more than one tool call
    to a Mistral assistant message correctly returns each tool call exactly
    once in the final payload.

    The current implementation uses a faulty for loop which produces N*N entries in the
    final tool_calls array of the payload (and thus duplicates tool call ids).
    """
    msg = AIMessage(
        content="",  # content should be blank when tool_calls are present
        tool_calls=[
            ToolCall(name="tool_a", args={"x": 1}, id="id_a", type="tool_call"),
            ToolCall(name="tool_b", args={"y": 2}, id="id_b", type="tool_call"),
        ],
        response_metadata={"model_provider": "mistralai"},
    )

    mistral_msg = _convert_message_to_mistral_chat_message(msg)

    assert mistral_msg["role"] == "assistant"
    assert "tool_calls" in mistral_msg, "Expected tool_calls to be present."

    tool_calls = mistral_msg["tool_calls"]
    # With the bug, this would be 4 (2x2); we expect exactly 2 entries.
    assert len(tool_calls) == 2, f"Expected 2 tool calls, got {len(tool_calls)}"

    # Ensure there are no duplicate ids
    ids = [tc.get("id") for tc in tool_calls if isinstance(tc, dict)]
    assert len(ids) == 2
    assert len(set(ids)) == 2, f"Duplicate tool call IDs found: {ids}"