def _session_messages_to_transcript(messages: list[ChatMessage]) -> str:
    """Convert session ChatMessages to JSONL transcript for ``--resume``.

    Reconstructs proper ``tool_use`` and ``tool_result`` content blocks from
    :attr:`ChatMessage.tool_calls` and :attr:`ChatMessage.tool_call_id` so the
    Claude CLI receives full structural context when no previous transcript file
    is available (e.g. first turn after a storage failure or compaction drop).

    This gives the model the same fidelity as an on-disk session JSONL file —
    preserving tool call names, IDs, inputs, and *complete* (un-truncated)
    tool results — rather than the lossy plain-text injection produced by
    :func:`_format_conversation_context` (which caps tool results at 500 chars
    and discards structural linkage).

    Args:
        messages: Prior session messages, typically ``session.messages[:-1]``
            (all turns except the current user query).

    Returns:
        A JSONL string suitable for writing to a temp file and passing as
        ``ClaudeAgentOptions.resume``.  Returns an empty string if the input
        list is empty after filtering compaction entries.
    """
    filtered = filter_compaction_messages(messages)
    if not filtered:
        return ""
    builder = TranscriptBuilder()
    for msg in filtered:
        if msg.role == "user" and msg.content:
            builder.append_user(msg.content)
        elif msg.role == "assistant":
            blocks: list[dict[str, Any]] = []
            if msg.content:
                blocks.append({"type": "text", "text": msg.content})
            for tc in msg.tool_calls or []:
                try:
                    tc_input: dict[str, Any] = json.loads(
                        tc.get("function", {}).get("arguments", "{}")
                    )
                except (json.JSONDecodeError, ValueError):
                    tc_input = {}
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": tc.get("function", {}).get("name", ""),
                        "input": tc_input,
                    }
                )
            if blocks:
                builder.append_assistant(blocks)
        elif msg.role == "tool":
            if msg.tool_call_id:
                builder.append_tool_result(
                    tool_use_id=msg.tool_call_id,
                    content=msg.content or "",
                )
            else:
                # Malformed tool message — no tool_call_id to link to an
                # assistant tool_use block.  Skip to avoid an unmatched
                # tool_result entry in the builder (which would confuse --resume).
                logger.warning("[SDK] Skipping tool gap message with no tool_call_id")
    return builder.to_jsonl()