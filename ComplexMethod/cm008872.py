def _validate_tool_call_message(message: BaseMessage) -> None:
    assert isinstance(message, AIMessage)
    assert len(message.tool_calls) == 1

    tool_call = message.tool_calls[0]
    assert tool_call["name"] == "magic_function"
    assert tool_call["args"] == {"input": 3}
    assert tool_call["id"] is not None
    assert tool_call.get("type") == "tool_call"

    content_tool_calls = [
        block for block in message.content_blocks if block["type"] == "tool_call"
    ]
    assert len(content_tool_calls) == 1
    content_tool_call = content_tool_calls[0]
    assert content_tool_call["name"] == "magic_function"
    assert content_tool_call["args"] == {"input": 3}
    assert content_tool_call["id"] is not None