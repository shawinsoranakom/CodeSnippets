def emit_content_delta_events(
    ctx: StreamingHarmonyContext,
    state: StreamingState,
) -> list[StreamingResponsesResponse]:
    """Emit events for content delta streaming based on channel type.

    This is a Harmony-specific dispatcher that extracts values from the
    Harmony context and delegates to shared leaf helpers.
    """
    delta = ctx.last_content_delta
    if not delta:
        return []

    channel = ctx.parser.current_channel
    recipient = ctx.parser.current_recipient

    if channel in ("final", "commentary") and recipient is None:
        # Preambles (commentary with no recipient) and final messages
        # are both user-visible text.
        return emit_text_delta_events(delta, state)
    elif channel == "analysis" and recipient is None:
        return emit_reasoning_delta_events(delta, state)
    # built-in tools will be triggered on the analysis channel
    # However, occasionally built-in tools will
    # still be output to commentary.
    elif channel in ("commentary", "analysis") and recipient is not None:
        if recipient.startswith("functions."):
            function_name = recipient[len("functions.") :]
            return emit_function_call_delta_events(delta, function_name, state)
        elif recipient == "python":
            return emit_code_interpreter_delta_events(delta, state)
        elif recipient.startswith("mcp.") or is_mcp_tool_by_namespace(recipient):
            return emit_mcp_delta_events(delta, state, recipient)

    return []