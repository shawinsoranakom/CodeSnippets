async def persist_pending_as_user_rows(
    session: "ChatSession",
    transcript_builder: "TranscriptBuilder",
    pending: list[PendingMessage],
    *,
    log_prefix: str,
    content_of: Callable[[PendingMessage], str] = lambda pm: pm.content,
    on_rollback: Callable[[int], None] | None = None,
) -> bool:
    """Append ``pending`` as user rows to *session* + *transcript_builder*,
    persist, and roll back + re-queue if the persist silently failed.

    This is the shared mid-turn follow-up persist used by both the baseline
    and SDK paths — they differ only in (a) how they derive the displayed
    string from a ``PendingMessage`` and (b) what extra per-path state
    (e.g. ``openai_messages``) needs trimming on rollback.  Those variance
    points are exposed as ``content_of`` and ``on_rollback``.

    Flow:
      1. Snapshot transcript + record the session.messages length.
      2. Append one user row per pending message to both stores.
      3. ``persist_session_safe`` — swallowed errors mean no sequences get
         back-filled, which we use as the failure signal.
      4. If any newly-appended row has ``sequence is None`` → rollback:
         delete the appended rows, restore the transcript snapshot, call
         ``on_rollback(anchor)`` for the caller's own state, then re-push
         each ``PendingMessage`` into the primary pending buffer so the
         next turn-start drain picks them up.

    Returns ``True`` when the rows were persisted with sequences, ``False``
    when the rollback path fired.  Callers can use this to decide whether
    to log success or continue a retry loop.
    """
    if not pending:
        return True

    session_anchor = len(session.messages)
    transcript_snapshot = transcript_builder.snapshot()

    for pm in pending:
        content = content_of(pm)
        session.messages.append(ChatMessage(role="user", content=content))
        transcript_builder.append_user(content=content)

    # ``persist_session_safe`` may return a ``model_copy`` of *session* (e.g.
    # when ``upsert_chat_session`` patches a concurrently-updated title).
    # Do NOT reassign the caller's reference — the caller already pushed the
    # rows into its own ``session.messages`` above, and rollback below MUST
    # delete from that same list.  Inspect the returned object only to learn
    # whether sequences were back-filled; if so, copy them onto the caller's
    # objects so the session stays internally consistent for downstream
    # ``append_and_save_message`` calls.
    persisted = await persist_session_safe(session, log_prefix)
    persisted_tail = persisted.messages[session_anchor:]
    if len(persisted_tail) == len(pending) and all(
        m.sequence is not None for m in persisted_tail
    ):
        for caller_msg, persisted_msg in zip(
            session.messages[session_anchor:], persisted_tail
        ):
            caller_msg.sequence = persisted_msg.sequence
    newly_appended = session.messages[session_anchor:]

    if any(m.sequence is None for m in newly_appended):
        logger.warning(
            "%s Mid-turn follow-up persist did not back-fill sequences; "
            "rolling back %d row(s) and re-queueing into the primary buffer",
            log_prefix,
            len(pending),
        )
        del session.messages[session_anchor:]
        transcript_builder.restore(transcript_snapshot)
        if on_rollback is not None:
            on_rollback(session_anchor)
        for pm in pending:
            try:
                await push_pending_message(session.session_id, pm)
            except Exception:
                logger.exception(
                    "%s Failed to re-queue mid-turn follow-up on rollback",
                    log_prefix,
                )
        return False

    logger.info(
        "%s Persisted %d mid-turn follow-up user row(s)",
        log_prefix,
        len(pending),
    )
    return True