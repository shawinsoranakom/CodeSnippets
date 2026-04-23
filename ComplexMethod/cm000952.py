def filter_compaction_messages(
    messages: list[ChatMessage],
) -> list[ChatMessage]:
    """Remove synthetic compaction tool-call messages (UI-only artifacts).

    Strips assistant messages whose only tool calls are compaction calls,
    and their corresponding tool-result messages.
    """
    compaction_ids: set[str] = set()
    filtered: list[ChatMessage] = []
    for msg in messages:
        if msg.role == "assistant" and msg.tool_calls:
            real_calls: list[dict[str, Any]] = []
            for tc in msg.tool_calls:
                if tc.get("function", {}).get("name") == COMPACTION_TOOL_NAME:
                    compaction_ids.add(tc.get("id", ""))
                else:
                    real_calls.append(tc)
            if not real_calls and not msg.content:
                continue
        if msg.role == "tool" and msg.tool_call_id in compaction_ids:
            continue
        filtered.append(msg)
    return filtered