def emit_tool_action_events(
    ctx: StreamingHarmonyContext,
    state: StreamingState,
    tool_server: ToolServer | None,
) -> list[StreamingResponsesResponse]:
    """Emit events for tool action turn."""
    if not ctx.is_assistant_action_turn() or len(ctx.parser.messages) == 0:
        return []

    events: list[StreamingResponsesResponse] = []
    previous_item = ctx.parser.messages[-1]

    # Handle browser tool
    if (
        tool_server is not None
        and tool_server.has_tool("browser")
        and previous_item.recipient is not None
        and previous_item.recipient.startswith("browser.")
    ):
        events.extend(emit_browser_tool_events(previous_item, state))

    # Handle tool completion
    if (
        tool_server is not None
        and previous_item.recipient is not None
        and state.current_item_id is not None
        and state.sent_output_item_added
    ):
        recipient = previous_item.recipient
        if recipient == "python":
            events.extend(emit_code_interpreter_completion_events(previous_item, state))
        elif recipient.startswith("mcp.") or is_mcp_tool_by_namespace(recipient):
            events.extend(
                emit_mcp_completion_events(
                    recipient, previous_item.content[0].text, state
                )
            )

    return events