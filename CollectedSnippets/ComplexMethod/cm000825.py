async def get_chat_messages_paginated(
    session_id: str,
    limit: int = 50,
    before_sequence: int | None = None,
    user_id: str | None = None,
) -> PaginatedMessages | None:
    """Get paginated messages for a session, newest first.

    Verifies session existence (and ownership when ``user_id`` is provided)
    in parallel with the message query.  Returns ``None`` when the session
    is not found or does not belong to the user.

    After fetching, a visibility guarantee ensures the page contains at least
    one user or assistant message.  If the entire page is tool messages (which
    are hidden in the UI), it expands backward until a visible message is found
    so the chat never appears blank.
    """
    # Build session-existence / ownership check
    session_where: ChatSessionWhereInput = {"id": session_id}
    if user_id is not None:
        session_where["userId"] = user_id

    # Build message include — fetch paginated messages in the same query
    msg_include: FindManyChatMessageArgsFromChatSession = {
        "order_by": {"sequence": "desc"},
        "take": limit + 1,
    }
    if before_sequence is not None:
        msg_include["where"] = {"sequence": {"lt": before_sequence}}

    # Single query: session existence/ownership + paginated messages
    session = await PrismaChatSession.prisma().find_first(
        where=session_where,
        include={"Messages": msg_include},
    )

    if session is None:
        return None

    session_info = ChatSessionInfo.from_db(session)
    results = list(session.Messages) if session.Messages else []

    has_more = len(results) > limit
    results = results[:limit]

    # Reverse to ascending order
    results.reverse()

    # Tool-call boundary fix: if the oldest message is a tool message,
    # expand backward to include the preceding assistant message that
    # owns the tool_calls, so convertChatSessionMessagesToUiMessages
    # can pair them correctly.
    if results and results[0].role == "tool":
        results, has_more = await _expand_tool_boundary(
            session_id, results, has_more, user_id
        )

    # Visibility guarantee: if the entire page has no user/assistant messages
    # (all tool messages), the chat would appear blank.  Expand backward
    # until we find at least one visible message.
    if results and not any(m.role in ("user", "assistant") for m in results):
        results, has_more = await _expand_for_visibility(
            session_id, results, has_more, user_id
        )

    messages = [ChatMessage.from_db(m) for m in results]
    oldest_sequence = messages[0].sequence if messages else None

    return PaginatedMessages(
        messages=messages,
        has_more=has_more,
        oldest_sequence=oldest_sequence,
        session=session_info,
    )