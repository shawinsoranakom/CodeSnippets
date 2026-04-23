def _build_provider_turn(state: OpenAIResponsesParseState) -> ProviderTurn:
    output_items = [
        state.output_items_by_index[idx]
        for idx in sorted(state.output_items_by_index.keys())
        if state.output_items_by_index.get(idx)
    ]

    tool_items = [
        item
        for item in output_items
        if isinstance(item, dict)
        and item.get("type") in ("function_call", "custom_tool_call")
    ]

    tool_calls: List[ToolCall] = []
    if tool_items:
        for item in tool_items:
            raw_args = item.get("arguments")
            if raw_args is None and item.get("type") == "custom_tool_call":
                raw_args = item.get("input")
            args, error = parse_json_arguments(raw_args)
            if error:
                args = {"INVALID_JSON": ensure_str(raw_args)}
            call_id = item.get("call_id") or item.get("id")
            tool_calls.append(
                ToolCall(
                    id=call_id or f"call-{uuid.uuid4().hex[:6]}",
                    name=item.get("name") or "unknown_tool",
                    arguments=args,
                )
            )
    else:
        for entry in state.tool_calls.values():
            args, error = parse_json_arguments(entry.get("arguments"))
            if error:
                args = {"INVALID_JSON": ensure_str(entry.get("arguments"))}
            call_id = entry.get("id") or entry.get("call_id")
            tool_calls.append(
                ToolCall(
                    id=call_id or f"call-{uuid.uuid4().hex[:6]}",
                    name=entry.get("name") or "unknown_tool",
                    arguments=args,
                )
            )

    assistant_turn: List[Dict[str, Any]] = output_items if tool_calls else []

    return ProviderTurn(
        assistant_text=state.assistant_text,
        tool_calls=tool_calls,
        assistant_turn=assistant_turn,
    )