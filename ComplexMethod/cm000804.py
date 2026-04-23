def format_pending_as_followup(pending: list[PendingMessage]) -> str:
    """Render drained pending messages as a ``<user_follow_up>`` block.

    Used by the SDK tool-boundary injection path to surface queued user
    text inside a tool result so the model reads it on the next LLM round,
    without starting a separate turn.  Wrapped in a stable XML-style tag so
    the shared system-prompt supplement can teach the model to treat the
    contents as the user's continuation of their request, not as tool
    output.  Each message is capped to keep the block bounded even if the
    user pastes long content.
    """
    if not pending:
        return ""
    rendered: list[str] = []
    total_chars = 0
    dropped = 0
    for idx, pm in enumerate(pending, start=1):
        text = pm.content
        if len(text) > _FOLLOWUP_CONTENT_MAX_CHARS:
            text = text[:_FOLLOWUP_CONTENT_MAX_CHARS] + "… [truncated]"
        entry = f"Message {idx}:\n{text}"
        if pm.context and pm.context.url:
            entry += f"\n[Page URL: {pm.context.url}]"
        if pm.file_ids:
            entry += "\n[Attached files: " + ", ".join(pm.file_ids) + "]"
        if total_chars + len(entry) > _FOLLOWUP_TOTAL_MAX_CHARS:
            dropped = len(pending) - idx + 1
            break
        rendered.append(entry)
        total_chars += len(entry)
    if dropped:
        rendered.append(f"… [{dropped} more message(s) truncated]")
    body = "\n\n".join(rendered)
    return (
        "<user_follow_up>\n"
        "The user sent the following message(s) while this tool was running. "
        "Treat them as a continuation of their current request — acknowledge "
        "and act on them in your next response. Do not echo these tags back.\n\n"
        f"{body}\n"
        "</user_follow_up>"
    )