def _already_terminal_result(sub: ChatSession) -> SessionResult | None:
    """Rebuild the aggregated result from the sub's persisted last turn,
    when the last message is a terminal assistant message.

    Lets ``get_sub_session_result`` short-circuit the subscribe+wait
    when the agent polls well after the sub actually finished (a common
    case when the user pauses and later asks "what's the result?").
    Returns ``None`` if the last message isn't terminal.
    """
    if not sub.messages:
        return None
    last = sub.messages[-1]
    if last.role != "assistant":
        return None
    if not last.content and not last.tool_calls:
        return None
    result = SessionResult()
    result.response_text = last.content or ""
    # Persisted tool calls are OpenAI-shape dicts; translate to
    # ToolCallEntry so the downstream ``response_from_outcome`` can
    # ``.model_dump()`` them uniformly with the live-drain path.
    for tc in last.tool_calls or []:
        fn = tc.get("function") or {}
        result.tool_calls.append(
            ToolCallEntry(
                tool_call_id=tc.get("id", ""),
                tool_name=fn.get("name") or tc.get("name") or "",
                input=fn.get("arguments") or tc.get("arguments") or tc.get("input"),
                output=tc.get("output"),
                success=tc.get("success"),
            )
        )
    return result