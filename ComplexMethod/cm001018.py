async def _build_progress_snapshot(
    inner_session_id: str | None,
) -> SubSessionProgressSnapshot | None:
    """Read the sub's ChatSession and return a preview of recent messages.

    Returns ``None`` silently on lookup failure — progress is best-effort;
    missing progress shouldn't abort the normal ``still running`` response.
    """
    if not inner_session_id:
        return None
    try:
        sub = await get_chat_session(inner_session_id)
        if sub is None:
            return None
        messages = list(sub.messages)
    except Exception as exc:  # best-effort peek
        logger.debug(
            "Progress snapshot unavailable for sub %s: %s",
            inner_session_id,
            exc,
        )
        return None

    tail = messages[-_PROGRESS_MESSAGE_LIMIT:]
    previews: list[dict[str, Any]] = []
    for msg in tail:
        content = getattr(msg, "content", "") or ""
        if not isinstance(content, str):
            try:
                content = json.dumps(content, default=str)
            except (TypeError, ValueError):
                content = str(content)
        if len(content) > _PROGRESS_CONTENT_PREVIEW_CHARS:
            content = content[:_PROGRESS_CONTENT_PREVIEW_CHARS] + "…"
        previews.append(
            {
                "role": getattr(msg, "role", "unknown"),
                "content": content,
            }
        )
    return SubSessionProgressSnapshot(
        message_count=len(messages),
        last_messages=previews,
    )