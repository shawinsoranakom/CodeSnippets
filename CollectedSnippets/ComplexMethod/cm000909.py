async def _build_query_message(
    current_message: str,
    session: ChatSession,
    use_resume: bool,
    transcript_msg_count: int,
    session_id: str,
    *,
    session_msg_ceiling: int | None = None,
    target_tokens: int | None = None,
    prior_messages: "list[ChatMessage] | None" = None,
) -> tuple[str, bool]:
    """Build the query message with appropriate context.

    When ``use_resume=True``, the CLI has the full session via ``--resume``;
    only a gap-fill prefix is injected when the transcript is stale.

    When ``use_resume=False``, the CLI starts a fresh session with no prior
    context, so the full prior session is always compressed and injected via
    ``_format_conversation_context``.  ``compress_context`` handles size
    reduction internally (LLM summarize → content truncate → middle-out delete
    → first/last trim).  ``target_tokens`` decreases on each retry to force
    progressively more aggressive compression when the first attempt exceeds
    context limits.

    Args:
        session_msg_ceiling: If provided, treat ``session.messages`` as if it
            only has this many entries when computing the gap slice.  Pass
            ``len(session.messages)`` captured *before* appending any pending
            messages so that mid-turn drains do not skew the gap calculation
            and cause pending messages to be duplicated in both the gap context
            and ``current_message``.

    Returns:
        Tuple of (query_message, was_compacted).
    """
    msg_count = len(session.messages)
    # Use the ceiling if supplied (prevents pending-message duplication when
    # messages were appended to session.messages after the drain but before
    # this function is called).
    effective_count = (
        session_msg_ceiling if session_msg_ceiling is not None else msg_count
    )
    # Exclude the current user message and any pending messages appended after
    # the ceiling snapshot — only history up to effective_count-1 is in scope.
    # max(0, ...) guards against a theoretical 0-message ceiling (brand-new
    # session) where -1 would select all-but-last instead of an empty slice.
    prior = session.messages[: max(0, effective_count - 1)]
    # ``role="reasoning"`` rows are persisted for frontend replay only and are
    # never present in the CLI JSONL (extended_thinking is embedded inside
    # assistant entries).  The watermark — ``transcript_msg_count`` — counts
    # non-reasoning rows (see _jsonl_covered upload), so we must filter reasoning
    # out of ``prior`` too; otherwise the ``prior[transcript_msg_count - 1]``
    # watermark-alignment check trips on a reasoning row (instead of the
    # expected assistant) and the gap injection is skipped, dropping real
    # mid-turn user rows from the next LLM query.
    prior = [m for m in prior if m.role != "reasoning"]

    logger.info(
        "[SDK] [%s] Context path: use_resume=%s, transcript_msg_count=%d,"
        " db_msg_count=%d, target_tokens=%s",
        session_id[:8],
        use_resume,
        transcript_msg_count,
        msg_count,
        target_tokens,
    )

    if use_resume and transcript_msg_count > 0:
        if transcript_msg_count < effective_count - 1:
            # Sanity-check the watermark: the last covered position should be
            # an assistant turn.  A user-role message here means the count is
            # misaligned (e.g. a message was deleted and DB positions shifted).
            # Skip the gap rather than injecting wrong context — the CLI session
            # loaded via --resume still has good history.
            if prior[transcript_msg_count - 1].role != "assistant":
                logger.warning(
                    "[SDK] [%s] Watermark misaligned: prior[%d].role=%r"
                    " (expected 'assistant') — skipping gap to avoid"
                    " injecting wrong context (transcript=%d, db=%d)",
                    session_id[:8],
                    transcript_msg_count - 1,
                    prior[transcript_msg_count - 1].role,
                    transcript_msg_count,
                    msg_count,
                )
                return current_message, False
            gap = prior[transcript_msg_count:]
            compressed, was_compressed = await _compress_messages(gap, target_tokens)
            gap_context = _format_conversation_context(compressed)
            if gap_context:
                logger.info(
                    "[SDK] Transcript stale: covers %d of %d messages, "
                    "gap=%d (compressed=%s), gap_context_bytes=%d",
                    transcript_msg_count,
                    msg_count,
                    len(gap),
                    was_compressed,
                    len(gap_context),
                )
                return (
                    f"{gap_context}\n\nNow, the user says:\n{current_message}",
                    was_compressed,
                )
            logger.warning(
                "[SDK] [%s] Transcript stale: gap produced empty context"
                " (%d msgs, transcript=%d/%d) — sending message without gap prefix",
                session_id[:8],
                len(gap),
                transcript_msg_count,
                msg_count,
            )
        else:
            logger.info(
                "[SDK] [%s] --resume covers full context (%d messages)",
                session_id[:8],
                transcript_msg_count,
            )
        return current_message, False

    elif not use_resume and effective_count > 1:
        # No --resume: the CLI starts a fresh session with no prior context.
        # Injecting only the post-transcript gap would omit the transcript-covered
        # prefix entirely, so always compress the full prior session here.
        # compress_context handles size reduction internally (LLM summarize →
        # content truncate → middle-out delete → first/last trim).

        # Final escape hatch: if the token budget is at or below the floor,
        # the model context is so tight that even fully compressed history
        # would risk a "prompt too long" error.  Return the bare message so
        # the user always gets a response rather than a hard failure.
        if target_tokens is not None and target_tokens <= _BARE_MESSAGE_TOKEN_FLOOR:
            logger.warning(
                "[SDK] [%s] target_tokens=%d at or below floor (%d) —"
                " skipping history injection to guarantee response delivery"
                " (session has %d messages)",
                session_id[:8],
                target_tokens,
                _BARE_MESSAGE_TOKEN_FLOOR,
                msg_count,
            )
            return current_message, False

        source = prior_messages if prior_messages is not None else prior
        logger.warning(
            "[SDK] [%s] No --resume for %d-message session — compressing context "
            "(source=%s, target_tokens=%s)",
            session_id[:8],
            msg_count,
            "transcript+gap" if prior_messages is not None else "full-db",
            target_tokens,
        )
        compressed, was_compressed = await _compress_messages(source, target_tokens)
        history_context = _format_conversation_context(compressed)
        if history_context:
            logger.info(
                "[SDK] [%s] Fallback context built: compressed=%s, context_bytes=%d",
                session_id[:8],
                was_compressed,
                len(history_context),
            )
            return (
                f"{history_context}\n\nNow, the user says:\n{current_message}",
                was_compressed,
            )
        logger.warning(
            "[SDK] [%s] Fallback context empty after compression"
            " (%d messages) — sending message without history",
            session_id[:8],
            len(source),
        )

    return current_message, False