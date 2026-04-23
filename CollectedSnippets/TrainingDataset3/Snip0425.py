async def update_tool_message_content(
    session_id: str,
    tool_call_id: str,
    new_content: str,
) -> bool:
    """Update the content of a tool message in chat history.

    Used by background tasks to update pending operation messages with final results.

    Args:
        session_id: The chat session ID.
        tool_call_id: The tool call ID to find the message.
        new_content: The new content to set.

    Returns:
        True if a message was updated, False otherwise.
    """
    try:
        result = await PrismaChatMessage.prisma().update_many(
            where={
                "sessionId": session_id,
                "toolCallId": tool_call_id,
            },
            data={
                "content": new_content,
            },
        )
        if result == 0:
            logger.warning(
                f"No message found to update for session {session_id}, "
                f"tool_call_id {tool_call_id}"
            )
            return False
        return True
    except Exception as e:
        logger.error(
            f"Failed to update tool message for session {session_id}, "
            f"tool_call_id {tool_call_id}: {e}"
        )
        return False
