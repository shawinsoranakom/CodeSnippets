async def parse_event(
    event: Any,
    state: OpenAIResponsesParseState,
    on_event: EventSink,
) -> None:
    event_type = _get_event_attr(event, "type")
    if event_type in (
        "response.created",
        "response.completed",
        "response.done",
        "response.output_item.done",
    ):
        if event_type == "response.completed":
            response = _get_event_attr(event, "response")
            if response:
                state.turn_usage = _extract_openai_usage(response)
        if event_type == "response.output_item.done":
            output_index = _get_event_attr(event, "output_index")
            item = _get_event_attr(event, "item")
            if isinstance(output_index, int) and item:
                state.output_items_by_index[output_index] = item
        return

    if event_type == "response.output_text.delta":
        delta = _get_event_attr(event, "delta", "")
        if delta:
            state.assistant_text += delta
            await on_event(StreamEvent(type="assistant_delta", text=delta))
        return

    if event_type in (
        "response.reasoning_text.delta",
        "response.reasoning_summary_text.delta",
    ):
        delta = _get_event_attr(event, "delta", "")
        if delta:
            if event_type == "response.reasoning_summary_text.delta":
                state.saw_reasoning_summary_text_delta = True
            await on_event(StreamEvent(type="thinking_delta", text=delta))
        return

    if event_type in (
        "response.reasoning_summary_part.added",
        "response.reasoning_summary_part.done",
    ):
        if state.saw_reasoning_summary_text_delta:
            return
        part = _get_event_attr(event, "part") or {}
        text = _get_event_attr(part, "text", "")
        if text and text != state.last_emitted_reasoning_summary_part:
            state.last_emitted_reasoning_summary_part = text
            await on_event(StreamEvent(type="thinking_delta", text=text))
        return

    if event_type == "response.output_item.added":
        item = _get_event_attr(event, "item")
        item_type = _get_event_attr(item, "type") if item else None
        output_index = _get_event_attr(event, "output_index")
        if isinstance(output_index, int) and item:
            state.output_items_by_index.setdefault(output_index, item)

        if item and item_type in ("function_call", "custom_tool_call"):
            item_id = _get_event_attr(item, "id")
            call_id = _get_event_attr(item, "call_id") or item_id
            if item_id and call_id:
                state.item_to_call_id[item_id] = call_id
            if call_id:
                if item_id and item_id in state.tool_calls and item_id != call_id:
                    existing = state.tool_calls.pop(item_id)
                    state.tool_calls[call_id] = {
                        **existing,
                        "id": call_id,
                    }
                args_value = _get_event_attr(item, "arguments")
                if args_value is None and item_type == "custom_tool_call":
                    args_value = _get_event_attr(item, "input")
                state.tool_calls.setdefault(
                    call_id,
                    {
                        "id": call_id,
                        "name": _get_event_attr(item, "name"),
                        "arguments": args_value or "",
                    },
                )
                if args_value:
                    await on_event(
                        StreamEvent(
                            type="tool_call_delta",
                            tool_call_id=call_id,
                            tool_name=_get_event_attr(item, "name"),
                            tool_arguments=args_value,
                        )
                    )
        return

    if event_type in (
        "response.function_call_arguments.delta",
        "response.mcp_call_arguments.delta",
        "response.custom_tool_call_input.delta",
    ):
        item_id = _get_event_attr(event, "item_id")
        call_id = _get_event_attr(event, "call_id")
        if call_id and item_id:
            state.item_to_call_id[item_id] = call_id
        if not call_id:
            call_id = state.item_to_call_id.get(item_id) if item_id else None
        if not call_id and item_id:
            call_id = item_id
        if not call_id:
            return

        entry = state.tool_calls.setdefault(
            call_id,
            {
                "id": call_id,
                "name": _get_event_attr(event, "name"),
                "arguments": "",
            },
        )
        delta_value = _get_event_attr(event, "delta")
        if delta_value is None:
            delta_value = _get_event_attr(event, "input")
        entry["arguments"] += ensure_str(delta_value)

        await on_event(
            StreamEvent(
                type="tool_call_delta",
                tool_call_id=call_id,
                tool_name=entry.get("name"),
                tool_arguments=entry.get("arguments"),
            )
        )
        return

    if event_type not in (
        "response.function_call_arguments.done",
        "response.mcp_call_arguments.done",
        "response.custom_tool_call_input.done",
    ):
        return

    item_id = _get_event_attr(event, "item_id")
    call_id = _get_event_attr(event, "call_id")
    if call_id and item_id:
        state.item_to_call_id[item_id] = call_id
    if not call_id:
        call_id = state.item_to_call_id.get(item_id) if item_id else None
    if not call_id and item_id:
        call_id = item_id
    if not call_id:
        return

    entry = state.tool_calls.setdefault(
        call_id,
        {
            "id": call_id,
            "name": _get_event_attr(event, "name"),
            "arguments": "",
        },
    )
    final_value = _get_event_attr(event, "arguments")
    if final_value is None:
        final_value = _get_event_attr(event, "input")
    if final_value is None:
        final_value = entry["arguments"]
    entry["arguments"] = final_value
    if _get_event_attr(event, "name"):
        entry["name"] = _get_event_attr(event, "name")

    await on_event(
        StreamEvent(
            type="tool_call_delta",
            tool_call_id=call_id,
            tool_name=entry.get("name"),
            tool_arguments=entry.get("arguments"),
        )
    )

    output_index = _get_event_attr(event, "output_index")
    if (
        item_id
        and isinstance(output_index, int)
        and isinstance(state.output_items_by_index.get(output_index), dict)
    ):
        state.output_items_by_index[output_index] = {
            **state.output_items_by_index[output_index],
            "arguments": entry["arguments"],
            "call_id": call_id,
            "name": entry.get("name"),
        }