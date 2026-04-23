async def compress_context(
    messages: list[dict],
    target_tokens: int | None = None,
    *,
    model: str = "gpt-4o",
    client: AsyncOpenAI | None = None,
    keep_recent: int = DEFAULT_KEEP_RECENT,
    reserve: int = 2_048,
    start_cap: int = 8_192,
    floor_cap: int = 128,
) -> CompressResult:
    """
    Unified context compression that combines summarization and truncation strategies.

    When ``target_tokens`` is None (the default), it is computed from the
    model's context window via ``get_compression_target(model)``.  This
    ensures large-context models (e.g. Opus 200K) retain more history
    while smaller models compress more aggressively.

    Strategy (in order):
    1. **LLM summarization** – If client provided, summarize old messages into a
       single context message while keeping recent messages intact. This is the
       primary strategy for chat service.
    2. **Content truncation** – Progressively halve a per-message cap and truncate
       bloated message content (tool outputs, large pastes). Preserves all messages
       but shortens their content. Primary strategy when client=None (LLM blocks).
    3. **Middle-out deletion** – Delete whole messages one at a time from the center
       outward, skipping tool messages and objective messages.
    4. **First/last trim** – Truncate first and last message content as last resort.

    Parameters
    ----------
    messages        Complete chat history (will be deep-copied).
    target_tokens   Hard ceiling for prompt size.
    model           Model name for tokenization and summarization.
    client          AsyncOpenAI client. If provided, enables LLM summarization
                    as the first strategy. If None, skips to truncation strategies.
    keep_recent     Number of recent messages to preserve during summarization.
    reserve         Tokens to reserve for model response.
    start_cap       Initial per-message truncation ceiling (tokens).
    floor_cap       Lowest cap before moving to deletions.

    Returns
    -------
    CompressResult with compressed messages and metadata.
    """
    # Resolve model-aware target when caller doesn't specify an explicit limit.
    if target_tokens is None:
        target_tokens = get_compression_target(model)

    # Guard clause for empty messages
    if not messages:
        return CompressResult(
            messages=[],
            token_count=0,
            was_compacted=False,
            original_token_count=0,
        )

    token_model = _normalize_model_for_tokenizer(model)
    enc = encoding_for_model(token_model)
    msgs = deepcopy(messages)

    def total_tokens() -> int:
        return sum(_msg_tokens(m, enc) for m in msgs)

    original_count = total_tokens()

    # Already under limit
    if original_count + reserve <= target_tokens:
        return CompressResult(
            messages=msgs,
            token_count=original_count,
            was_compacted=False,
            original_token_count=original_count,
        )

    messages_summarized = 0
    messages_dropped = 0

    # ---- STEP 1: LLM summarization (if client provided) -------------------
    # This is the primary compression strategy for chat service.
    # Summarize old messages while keeping recent ones intact.
    if client is not None:
        has_system = len(msgs) > 0 and msgs[0].get("role") == "system"
        system_msg = msgs[0] if has_system else None

        # Calculate old vs recent messages
        if has_system:
            if len(msgs) > keep_recent + 1:
                old_msgs = msgs[1:-keep_recent]
                recent_msgs = msgs[-keep_recent:]
            else:
                old_msgs = []
                recent_msgs = msgs[1:] if len(msgs) > 1 else []
        else:
            if len(msgs) > keep_recent:
                old_msgs = msgs[:-keep_recent]
                recent_msgs = msgs[-keep_recent:]
            else:
                old_msgs = []
                recent_msgs = msgs

        # Ensure tool pairs stay intact
        slice_start = max(0, len(msgs) - keep_recent)
        recent_msgs = _ensure_tool_pairs_intact(recent_msgs, msgs, slice_start)

        if old_msgs:
            try:
                summary_text = await _summarize_messages_llm(old_msgs, client, model)
                summary_msg = {
                    "role": "assistant",
                    "content": f"[Previous conversation summary — for context only]: {summary_text}",
                }
                messages_summarized = len(old_msgs)

                if has_system:
                    msgs = [system_msg, summary_msg] + recent_msgs
                else:
                    msgs = [summary_msg] + recent_msgs

                logger.info(
                    "Context summarized: %d -> %d tokens, summarized %d messages",
                    original_count,
                    total_tokens(),
                    messages_summarized,
                )
            except Exception as e:
                logger.warning(
                    "Summarization failed, continuing with truncation: %s", e
                )
                # Fall through to content truncation

    # ---- STEP 2: Normalize content ----------------------------------------
    # Convert non-string payloads to strings so token counting is coherent.
    # Always run this before truncation to ensure consistent token counting.
    for i, m in enumerate(msgs):
        if not isinstance(m.get("content"), str) and m.get("content") is not None:
            if _is_tool_message(m):
                continue
            if i == 0 or i == len(msgs) - 1:
                continue
            content_str = json.dumps(m["content"], separators=(",", ":"))
            if len(content_str) > 20_000:
                content_str = _truncate_middle_tokens(content_str, enc, 20_000)
            m["content"] = content_str

    # ---- STEP 3: Token-aware content truncation ---------------------------
    # Progressively halve per-message cap and truncate bloated content.
    # This preserves all messages but shortens their content.
    cap = start_cap
    while total_tokens() + reserve > target_tokens and cap >= floor_cap:
        for m in msgs[1:-1]:
            if _is_tool_message(m):
                _truncate_tool_message_content(m, enc, cap)
                continue
            if _is_objective_message(m):
                continue
            content = m.get("content") or ""
            if _tok_len(content, enc) > cap:
                m["content"] = _truncate_middle_tokens(content, enc, cap)
        cap //= 2

    # ---- STEP 4: Middle-out deletion --------------------------------------
    # Delete messages one at a time from the center outward.
    # This is more granular than dropping all old messages at once.
    while total_tokens() + reserve > target_tokens and len(msgs) > 2:
        deletable: list[int] = []
        for i in range(1, len(msgs) - 1):
            msg = msgs[i]
            if (
                msg is not None
                and not _is_tool_message(msg)
                and not _is_objective_message(msg)
            ):
                deletable.append(i)
        if not deletable:
            break
        centre = len(msgs) // 2
        to_delete = min(deletable, key=lambda i: abs(i - centre))
        del msgs[to_delete]
        messages_dropped += 1

    # ---- STEP 5: Final trim on first/last ---------------------------------
    cap = start_cap
    while total_tokens() + reserve > target_tokens and cap >= floor_cap:
        for idx in (0, -1):
            msg = msgs[idx]
            if msg is None:
                continue
            if _is_tool_message(msg):
                _truncate_tool_message_content(msg, enc, cap)
                continue
            text = msg.get("content") or ""
            if _tok_len(text, enc) > cap:
                msg["content"] = _truncate_middle_tokens(text, enc, cap)
        cap //= 2

    # Filter out any None values that may have been introduced
    final_msgs: list[dict] = [m for m in msgs if m is not None]

    # ---- STEP 6: Final tool-pair validation ---------------------------------
    # After all compression steps, verify that every tool response has a
    # matching tool_call in a preceding assistant message. Remove orphans
    # to prevent API errors (e.g., Anthropic's "unexpected tool_use_id").
    final_msgs = validate_and_remove_orphan_tool_responses(final_msgs)

    final_count = sum(_msg_tokens(m, enc) for m in final_msgs)
    error = None
    if final_count + reserve > target_tokens:
        error = f"Could not compress below target ({final_count + reserve} > {target_tokens})"
        logger.warning(error)

    return CompressResult(
        messages=final_msgs,
        token_count=final_count,
        was_compacted=True,
        error=error,
        original_token_count=original_count,
        messages_summarized=messages_summarized,
        messages_dropped=messages_dropped,
    )