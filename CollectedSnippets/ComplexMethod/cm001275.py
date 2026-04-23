async def get_session(
    session_id: str,
    user_id: Annotated[str, Security(auth.get_user_id)],
    limit: int = Query(default=50, ge=1, le=200),
    before_sequence: int | None = Query(default=None, ge=0),
) -> SessionDetailResponse:
    """
    Retrieve the details of a specific chat session.

    Supports cursor-based pagination via ``limit`` and ``before_sequence``.
    When no pagination params are provided, returns the most recent messages.
    """
    page = await get_chat_messages_paginated(
        session_id, limit, before_sequence, user_id=user_id
    )
    if page is None:
        raise NotFoundError(f"Session {session_id} not found.")

    messages = [
        _strip_injected_context(message.model_dump()) for message in page.messages
    ]

    # Only check active stream on initial load (not on "load more" requests)
    active_stream_info = None
    if before_sequence is None:
        active_session, last_message_id = await stream_registry.get_active_session(
            session_id, user_id
        )
        if active_session:
            active_stream_info = ActiveStreamInfo(
                turn_id=active_session.turn_id,
                last_message_id=last_message_id,
            )

    # Skip session metadata on "load more" — frontend only needs messages
    if before_sequence is not None:
        return SessionDetailResponse(
            id=page.session.session_id,
            created_at=page.session.started_at.isoformat(),
            updated_at=page.session.updated_at.isoformat(),
            user_id=page.session.user_id or None,
            messages=messages,
            active_stream=None,
            has_more_messages=page.has_more,
            oldest_sequence=page.oldest_sequence,
            total_prompt_tokens=0,
            total_completion_tokens=0,
        )

    total_prompt = sum(u.prompt_tokens for u in page.session.usage)
    total_completion = sum(u.completion_tokens for u in page.session.usage)

    return SessionDetailResponse(
        id=page.session.session_id,
        created_at=page.session.started_at.isoformat(),
        updated_at=page.session.updated_at.isoformat(),
        user_id=page.session.user_id or None,
        messages=messages,
        active_stream=active_stream_info,
        has_more_messages=page.has_more,
        oldest_sequence=page.oldest_sequence,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        metadata=page.session.metadata,
    )