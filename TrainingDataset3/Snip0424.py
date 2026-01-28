async def add_chat_messages_batch(
    session_id: str,
    messages: list[dict[str, Any]],
    start_sequence: int,
) -> list[PrismaChatMessage]:
    """Add multiple messages to a chat session in a batch.

    Uses a transaction for atomicity - if any message creation fails,
    the entire batch is rolled back.
    """
    if not messages:
        return []

    created_messages = []

    async with transaction() as tx:
        for i, msg in enumerate(messages):
            # Build input dict dynamically rather than using ChatMessageCreateInput
            # directly because Prisma's TypedDict validation rejects optional fields
            # set to None. We only include fields that have values, then cast.
            data: dict[str, Any] = {
                "Session": {"connect": {"id": session_id}},
                "role": msg["role"],
                "sequence": start_sequence + i,
            }

            # Add optional string fields
            if msg.get("content") is not None:
                data["content"] = msg["content"]
            if msg.get("name") is not None:
                data["name"] = msg["name"]
            if msg.get("tool_call_id") is not None:
                data["toolCallId"] = msg["tool_call_id"]
            if msg.get("refusal") is not None:
                data["refusal"] = msg["refusal"]

            # Add optional JSON fields only when they have values
            if msg.get("tool_calls") is not None:
                data["toolCalls"] = SafeJson(msg["tool_calls"])
            if msg.get("function_call") is not None:
                data["functionCall"] = SafeJson(msg["function_call"])

            created = await PrismaChatMessage.prisma(tx).create(
                data=cast(ChatMessageCreateInput, data)
            )
            created_messages.append(created)

        # Update session's updatedAt timestamp within the same transaction.
        # Note: Token usage (total_prompt_tokens, total_completion_tokens) is updated
        # separately via update_chat_session() after streaming completes.
        await PrismaChatSession.prisma(tx).update(
            where={"id": session_id},
            data={"updatedAt": datetime.now(UTC)},
        )

    return created_messages
