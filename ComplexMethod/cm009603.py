def _convert_to_v1_from_bedrock_chunk(
    message: AIMessageChunk,
) -> list[types.ContentBlock]:
    """Convert bedrock message chunk content to v1 format."""
    if (
        message.content == ""
        and not message.additional_kwargs
        and not message.tool_calls
    ):
        # Bedrock outputs multiple chunks containing response metadata
        return []

    out = _convert_to_v1_from_anthropic(message)

    if (
        message.tool_call_chunks
        and not message.content
        and message.chunk_position != "last"  # keep tool_calls if aggregated
    ):
        for tool_call_chunk in message.tool_call_chunks:
            tc: types.ToolCallChunk = {
                "type": "tool_call_chunk",
                "id": tool_call_chunk.get("id"),
                "name": tool_call_chunk.get("name"),
                "args": tool_call_chunk.get("args"),
            }
            if (idx := tool_call_chunk.get("index")) is not None:
                tc["index"] = idx
            out.append(tc)
    return out