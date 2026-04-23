async def _compress_messages(
    messages: list[ChatMessage],
    target_tokens: int | None = None,
) -> tuple[list[ChatMessage], bool]:
    """Compress a list of messages if they exceed the token threshold.

    Delegates to `_run_compression` (`transcript.py`) which centralizes
    the "try LLM, fallback to truncation" pattern with timeouts.  Both
    `_compress_messages` and `compact_transcript` share this helper so
    client acquisition and error handling are consistent.

    ``target_tokens`` sets a hard ceiling for the compressed output so
    callers can enforce a tighter budget on retries.  When ``None``,
    ``compress_context`` uses the model-aware default.

    See also:
        `_run_compression` — shared compression with timeout guards.
        `compact_transcript` — compresses JSONL transcript entries.
        `CompactionTracker` — emits UI events for mid-stream compaction.
    """
    # ``role="reasoning"`` rows are persisted for frontend replay only — they
    # aren't valid OpenAI roles and ``compress_context`` would either drop or
    # malform them.  Strip here so every caller is covered (``_build_query_message``
    # already filters upstream, but ``_seed_transcript`` and any future caller
    # don't, and centralising the filter avoids per-call-site drift).
    messages = [
        m for m in filter_compaction_messages(messages) if m.role != "reasoning"
    ]

    if len(messages) < 2:
        return messages, False

    # Convert ChatMessages to dicts for compress_context
    messages_dict = []
    for msg in messages:
        msg_dict: dict[str, Any] = {"role": msg.role}
        if msg.content:
            msg_dict["content"] = msg.content
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls
        if msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id
        messages_dict.append(msg_dict)

    try:
        result = await _run_compression(
            messages_dict,
            config.thinking_standard_model,
            "[SDK]",
            target_tokens=target_tokens,
        )
    except Exception as exc:
        # Guard against timeouts or unexpected errors in compression —
        # return the original messages so the caller can proceed without
        # compaction rather than propagating the error to the retry loop.
        logger.warning("[SDK] _compress_messages failed, returning originals: %s", exc)
        return messages, False

    if result.was_compacted:
        logger.info(
            "[SDK] Context compacted: %d -> %d tokens (%d summarized, %d dropped)",
            result.original_token_count,
            result.token_count,
            result.messages_summarized,
            result.messages_dropped,
        )
        # Convert compressed dicts back to ChatMessages
        return [
            ChatMessage(
                role=m["role"],
                content=m.get("content"),
                tool_calls=m.get("tool_calls"),
                tool_call_id=m.get("tool_call_id"),
            )
            for m in result.messages
        ], True

    return messages, False