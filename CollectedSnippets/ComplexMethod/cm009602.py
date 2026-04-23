def _convert_to_v1_from_bedrock(message: AIMessage) -> list[types.ContentBlock]:
    """Convert bedrock message content to v1 format."""
    out = _convert_to_v1_from_anthropic(message)

    content_tool_call_ids = {
        block.get("id")
        for block in out
        if isinstance(block, dict) and block.get("type") == "tool_call"
    }
    for tool_call in message.tool_calls:
        if (id_ := tool_call.get("id")) and id_ not in content_tool_call_ids:
            tool_call_block: types.ToolCall = {
                "type": "tool_call",
                "id": id_,
                "name": tool_call["name"],
                "args": tool_call["args"],
            }
            if "index" in tool_call:
                tool_call_block["index"] = tool_call["index"]  # type: ignore[typeddict-item]
            if "extras" in tool_call:
                tool_call_block["extras"] = tool_call["extras"]  # type: ignore[typeddict-item]
            out.append(tool_call_block)
    return out