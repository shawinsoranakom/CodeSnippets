def _format_conversation_context(messages: list[ChatMessage]) -> str | None:
    """Format conversation messages into a context prefix for the user message.

    Includes user messages, assistant text, tool call summaries, and
    tool result summaries so the agent retains full context about what
    tools were invoked and their outcomes.

    Returns None if there are no messages to format.
    """
    if not messages:
        return None

    # Filter out compaction messages first, then format
    messages = filter_compaction_messages(messages)

    lines: list[str] = []
    for msg in messages:
        if msg.role == "user":
            if msg.content:
                lines.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            if msg.content:
                lines.append(f"You responded: {msg.content}")
            # Omit tool_calls — any text representation gets mimicked
            # by the model. Tool results below provide the context.
        elif msg.role == "tool":
            content = msg.content or ""
            lines.append(f"Tool output: {content[:500]}")

    if not lines:
        return None

    return "<conversation_history>\n" + "\n".join(lines) + "\n</conversation_history>"