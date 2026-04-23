async def add_chat_messages_batch(
    session_id: str,
    messages: list[dict[str, Any]],
    start_sequence: int,
) -> int:
    """Add multiple messages to a chat session in a batch.

    Uses collision detection with retry: tries to create messages starting
    at start_sequence. If a unique constraint violation occurs (e.g., the
    streaming loop and long-running callback race), queries the latest
    sequence and retries with the correct offset. This avoids unnecessary
    upserts and DB queries in the common case (no collision).

    Returns:
        Next sequence number for the next message to be inserted. This equals
        start_sequence + len(messages) and allows callers to update their
        counters even when collision detection adjusts start_sequence.
    """
    if not messages:
        # No messages to add - return current count
        return start_sequence

    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Single timestamp for all messages and session update
            now = datetime.now(UTC)

            async with db.transaction() as tx:
                # Build all message data
                messages_data = []
                for i, msg in enumerate(messages):
                    # Build ChatMessageCreateInput with only non-None values
                    # (Prisma TypedDict rejects optional fields set to None)
                    # Note: create_many doesn't support nested creates, use sessionId directly
                    data: ChatMessageCreateInput = {
                        "sessionId": session_id,
                        "role": msg["role"],
                        "sequence": start_sequence + i,
                        "createdAt": now,
                    }

                    # Add optional string fields — sanitize to strip
                    # PostgreSQL-incompatible control characters.
                    if msg.get("content") is not None:
                        data["content"] = sanitize_string(msg["content"])
                    if msg.get("name") is not None:
                        data["name"] = msg["name"]
                    if msg.get("tool_call_id") is not None:
                        data["toolCallId"] = msg["tool_call_id"]
                    if msg.get("refusal") is not None:
                        data["refusal"] = sanitize_string(msg["refusal"])

                    # Add optional JSON fields only when they have values
                    if msg.get("tool_calls") is not None:
                        data["toolCalls"] = SafeJson(msg["tool_calls"])
                    if msg.get("function_call") is not None:
                        data["functionCall"] = SafeJson(msg["function_call"])

                    if msg.get("duration_ms") is not None:
                        data["durationMs"] = msg["duration_ms"]

                    messages_data.append(data)

                # Run create_many and session update in parallel within transaction
                # Both use the same timestamp for consistency
                await asyncio.gather(
                    PrismaChatMessage.prisma(tx).create_many(data=messages_data),
                    PrismaChatSession.prisma(tx).update(
                        where={"id": session_id},
                        data={"updatedAt": now},
                    ),
                )

            # Return next sequence number for counter sync
            return start_sequence + len(messages)

        except UniqueViolationError:
            if attempt < max_retries - 1:
                # Collision detected - query MAX(sequence)+1 and retry with correct offset
                logger.info(
                    f"Collision detected for session {session_id} at sequence "
                    f"{start_sequence}, querying DB for latest sequence"
                )
                start_sequence = await get_next_sequence(session_id)
                logger.info(
                    f"Retrying batch insert with start_sequence={start_sequence}"
                )
                continue
            else:
                # Max retries exceeded - propagate error
                raise

    # Should never reach here due to raise in exception handler
    raise RuntimeError(f"Failed to insert messages after {max_retries} attempts")