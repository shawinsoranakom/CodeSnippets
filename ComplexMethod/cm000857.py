async def _save_session_to_db(
    session: ChatSession,
    existing_message_count: int,
    *,
    skip_existence_check: bool = False,
) -> None:
    """Save or update a chat session in the database.

    Args:
        skip_existence_check: When True, skip the ``get_chat_session`` query
            and assume the session row already exists.  Saves one DB round trip
            for incremental saves during streaming.
    """
    db = chat_db()

    if not skip_existence_check:
        # Check if session exists in DB
        existing = await db.get_chat_session(session.session_id)

        if not existing:
            # Create new session
            await db.create_chat_session(
                session_id=session.session_id,
                user_id=session.user_id,
                metadata=session.metadata,
            )
            existing_message_count = 0

    # Calculate total tokens from usage
    total_prompt = sum(u.prompt_tokens for u in session.usage)
    total_completion = sum(u.completion_tokens for u in session.usage)

    # Update session metadata
    await db.update_chat_session(
        session_id=session.session_id,
        credentials=session.credentials,
        successful_agent_runs=session.successful_agent_runs,
        successful_agent_schedules=session.successful_agent_schedules,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
    )

    # Add new messages (only those after existing count)
    new_messages = session.messages[existing_message_count:]
    if new_messages:
        messages_data = []
        for msg in new_messages:
            messages_data.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name,
                    "tool_call_id": msg.tool_call_id,
                    "refusal": msg.refusal,
                    "tool_calls": msg.tool_calls,
                    "function_call": msg.function_call,
                }
            )
        logger.info(
            f"Saving {len(new_messages)} new messages to DB for session {session.session_id}: "
            f"roles={[m['role'] for m in messages_data]}, "
            f"start_sequence={existing_message_count}"
        )
        await db.add_chat_messages_batch(
            session_id=session.session_id,
            messages=messages_data,
            start_sequence=existing_message_count,
        )

        # Back-fill sequence numbers on the in-memory ChatMessage objects so
        # that downstream callers (inject_user_context) can persist updates
        # by sequence rather than falling back to index-based writes.
        for i, msg in enumerate(new_messages):
            msg.sequence = existing_message_count + i