async def inject_user_context(
    understanding: BusinessUnderstanding | None,
    message: str,
    session_id: str,
    session_messages: list[ChatMessage],
    warm_ctx: str = "",
    env_ctx: str = "",
) -> str | None:
    """Prepend trusted context blocks to the first user message.

    Builds the first-turn message in this order (all optional):
    ``<memory_context>`` → ``<env_context>`` → ``<user_context>`` → sanitised user text.

    Updates the in-memory session_messages list and persists the prefixed
    content to the DB so resumed sessions and page reloads retain
    personalisation.

    Untrusted input — both the user-supplied ``message`` and the user-owned
    fields inside ``understanding`` — is stripped/escaped before being placed
    inside the trusted ``<user_context>`` block. This prevents a user from
    spoofing their own (or another user's) personalisation context by
    supplying a literal ``<user_context>...</user_context>`` tag in the
    message body or in any of their understanding fields.

    When ``understanding`` is ``None``, no trusted context is wrapped but the
    first user message is still sanitised in place so that attacker tags
    typed by new users do not reach the LLM.

    Args:
        understanding: Business context fetched from the DB, or ``None``.
        message: The raw user-supplied message text (may contain attacker tags).
        session_id: Used as the DB key for persisting the updated content.
        session_messages: The in-memory message list for the current session.
        warm_ctx: Trusted Graphiti warm-context string to inject as a
            ``<memory_context>`` block before the ``<user_context>`` prefix.
            Passed as server-side data — never sanitised (caller is responsible
            for ensuring the value is not user-supplied).  Empty string → block
            is omitted.
        env_ctx: Trusted environment context string to inject as an
            ``<env_context>`` block (e.g. working directory).  Prepended AFTER
            ``sanitize_user_supplied_context`` runs so the server-injected block
            is never stripped by the sanitizer.  Empty string → block is omitted.

    Returns:
        ``str`` -- the sanitised (and optionally prefixed) message when
        ``session_messages`` contains at least one user-role message.
        This is **always a non-empty string** when a user message exists,
        even if the content is unchanged (i.e. no attacker tags were found
        and no understanding was injected).  Callers should therefore
        **not** use ``if result is not None`` as a proxy for "something
        changed" -- use it only to detect "no user message was present".

        ``None`` -- only when ``session_messages`` contains **no** user-role
        message at all.
    """
    # The SDK and baseline services call strip_user_context_tags (an alias for
    # sanitize_user_supplied_context) at their entry points on every turn, so
    # `message` is already clean when inject_user_context is reached on turn 1.
    # The call below is therefore technically redundant for those callers, but
    # it is kept so that this function remains safe to call directly (e.g. from
    # tests) without prior sanitization — and because the operation is
    # idempotent (a second pass over already-clean text is a no-op).
    sanitized_message = sanitize_user_supplied_context(message)

    if understanding is None:
        # No trusted context to inject — but we still need to persist the
        # sanitised message so a later resume / page-reload replay doesn't
        # feed the attacker tags back into the LLM.
        final_message = sanitized_message
    else:
        raw_ctx = format_understanding_for_prompt(understanding)
        if not raw_ctx:
            # All BusinessUnderstanding fields are empty/None — injecting an
            # empty <user_context>\n\n</user_context> block adds no value and
            # wastes tokens. Fall back to the bare sanitized message instead.
            final_message = sanitized_message
        else:
            # _sanitize_user_context_field is applied to the combined output of
            # format_understanding_for_prompt rather than to each individual
            # field. This is intentional: format_understanding_for_prompt
            # produces a single structured string from trusted DB data, so the
            # trust boundary is at the DB read, not at each field boundary.
            # Sanitizing at the combined level is both correct and sufficient —
            # it strips any residual tag-like sequences before the string is
            # wrapped in the <user_context> block that the LLM sees.
            user_ctx = _sanitize_user_context_field(raw_ctx)
            final_message = format_user_context_prefix(user_ctx) + sanitized_message

    # Prepend environment context AFTER sanitization so the server-injected
    # block is never stripped by sanitize_user_supplied_context.
    if env_ctx:
        final_message = (
            f"<{ENV_CONTEXT_TAG}>\n{env_ctx}\n</{ENV_CONTEXT_TAG}>\n\n" + final_message
        )
    # Prepend Graphiti warm context as a <memory_context> block AFTER sanitization
    # so that the trusted server-injected block is never stripped by
    # sanitize_user_supplied_context (which removes attacker-supplied tags).
    # This must be the outermost prefix so the LLM sees memory context first.
    if warm_ctx:
        final_message = (
            f"<{MEMORY_CONTEXT_TAG}>\n{warm_ctx}\n</{MEMORY_CONTEXT_TAG}>\n\n"
            + final_message
        )

    # Scan in reverse so we target the current turn's user message, not
    # an older one that may exist when pending messages have been drained.
    for session_msg in reversed(session_messages):
        if session_msg.role == "user":
            # Only touch the DB / in-memory state when the content actually
            # needs to change — avoids an unnecessary write on the common
            # "no attacker tag, no understanding" path.
            if session_msg.content != final_message:
                session_msg.content = final_message
                if session_msg.sequence is not None:
                    await chat_db().update_message_content_by_sequence(
                        session_id, session_msg.sequence, final_message
                    )
                else:
                    logger.warning(
                        f"[inject_user_context] Cannot persist user context for session "
                        f"{session_id}: first user message has no sequence number"
                    )
            return final_message
    return None