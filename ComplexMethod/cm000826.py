async def update_chat_session(
    session_id: str,
    credentials: dict[str, Any] | None = None,
    successful_agent_runs: dict[str, Any] | None = None,
    successful_agent_schedules: dict[str, Any] | None = None,
    total_prompt_tokens: int | None = None,
    total_completion_tokens: int | None = None,
    title: str | None = None,
) -> ChatSession | None:
    """Update a chat session's mutable fields.

    Note: ``metadata`` (which includes ``dry_run``) is intentionally omitted —
    it is set once at creation time and treated as immutable for the lifetime
    of the session.
    """
    data: ChatSessionUpdateInput = {"updatedAt": datetime.now(UTC)}

    if credentials is not None:
        data["credentials"] = SafeJson(credentials)
    if successful_agent_runs is not None:
        data["successfulAgentRuns"] = SafeJson(successful_agent_runs)
    if successful_agent_schedules is not None:
        data["successfulAgentSchedules"] = SafeJson(successful_agent_schedules)
    if total_prompt_tokens is not None:
        data["totalPromptTokens"] = total_prompt_tokens
    if total_completion_tokens is not None:
        data["totalCompletionTokens"] = total_completion_tokens
    if title is not None:
        data["title"] = title

    session = await PrismaChatSession.prisma().update(
        where={"id": session_id},
        data=data,
        include={"Messages": {"order_by": {"sequence": "asc"}}},
    )
    return ChatSession.from_db(session) if session else None