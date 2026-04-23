def emit_previous_item_done_events(
    previous_item: HarmonyMessage,
    state: StreamingState,
) -> list[StreamingResponsesResponse]:
    """Emit done events for the previous item when expecting a new start.

    This is a Harmony-specific dispatcher that extracts values from the
    Harmony parser's message object and delegates to shared leaf helpers.
    """
    text = previous_item.content[0].text
    if previous_item.recipient is not None:
        # Deal with tool call
        if previous_item.recipient.startswith("functions."):
            function_name = previous_item.recipient[len("functions.") :]
            return emit_function_call_done_events(function_name, text, state)
        elif previous_item.recipient == "python":
            return emit_code_interpreter_completion_events(previous_item, state)
        elif (
            is_mcp_tool_by_namespace(previous_item.recipient)
            and state.current_item_id is not None
            and state.current_item_id.startswith("mcp_")
        ):
            return emit_mcp_completion_events(previous_item.recipient, text, state)
    elif previous_item.channel == "analysis":
        return emit_reasoning_done_events(text, state)
    elif previous_item.channel in ("commentary", "final"):
        # Preambles (commentary with no recipient) and final messages
        # are both user-visible text.
        return emit_text_output_done_events(text, state)
    return []