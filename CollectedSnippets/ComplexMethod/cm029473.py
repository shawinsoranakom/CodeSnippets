async def _parse_stream_event(
    event: Any,
    state: AnthropicParseState,
    on_event: EventSink,
) -> None:
    if event.type == "content_block_start":
        block = event.content_block
        if getattr(block, "type", None) != "tool_use":
            return

        tool_id = getattr(block, "id", None) or f"tool-{uuid.uuid4().hex[:6]}"
        tool_name = getattr(block, "name", None) or "unknown_tool"
        args = getattr(block, "input", None)
        state.tool_blocks[event.index] = {
            "id": tool_id,
            "name": tool_name,
        }
        state.tool_json_buffers[event.index] = ""
        if args:
            await on_event(
                StreamEvent(
                    type="tool_call_delta",
                    tool_call_id=tool_id,
                    tool_name=tool_name,
                    tool_arguments=args,
                )
            )
        return

    if event.type != "content_block_delta":
        return

    if event.delta.type == "thinking_delta":
        await on_event(StreamEvent(type="thinking_delta", text=event.delta.thinking))
        return

    if event.delta.type == "text_delta":
        state.assistant_text += event.delta.text
        await on_event(StreamEvent(type="assistant_delta", text=event.delta.text))
        return

    if event.delta.type != "input_json_delta":
        return

    partial_json = getattr(event.delta, "partial_json", None) or ""
    if not partial_json:
        return

    buffer = state.tool_json_buffers.get(event.index, "") + partial_json
    state.tool_json_buffers[event.index] = buffer
    meta = state.tool_blocks.get(event.index)
    if not meta:
        return

    await on_event(
        StreamEvent(
            type="tool_call_delta",
            tool_call_id=meta.get("id"),
            tool_name=meta.get("name"),
            tool_arguments=buffer,
        )
    )