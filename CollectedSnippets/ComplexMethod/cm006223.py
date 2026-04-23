async def aadd_messagetables(messages: list[MessageTable], session: AsyncSession, retry_count: int = 0):
    """Add messages to the database with retry logic for CancelledError.

    Args:
        messages: List of MessageTable objects to add
        session: Database session
        retry_count: Internal retry counter (max 3 retries to prevent infinite loops)

    This function includes a workaround for CancelledError that can occur during
    session.commit() when called from build_public_tmp but not from build_flow.
    The retry mechanism has a limit to prevent infinite recursion.
    """
    max_retries = 3
    try:
        try:
            for message in messages:
                result = session.add(message)
                if asyncio.iscoroutine(result):
                    await result
            await session.commit()
            # This is a hack.
            # We are doing this because build_public_tmp causes the CancelledError to be raised
            # while build_flow does not.
        except asyncio.CancelledError:
            await session.rollback()
            if retry_count >= max_retries:
                await logger.awarning(
                    f"Max retries ({max_retries}) reached for aadd_messagetables due to CancelledError"
                )
                error_msg = "Add Message operation cancelled after multiple retries"
                raise ValueError(error_msg) from None
            return await aadd_messagetables(messages, session, retry_count + 1)
        for message in messages:
            await session.refresh(message)
    except asyncio.CancelledError as e:
        await logger.aexception(e)
        error_msg = "Operation cancelled"
        raise ValueError(error_msg) from e
    except Exception as e:
        await logger.aexception(e)
        raise

    new_messages = []
    for msg in messages:
        msg.properties = json.loads(msg.properties) if isinstance(msg.properties, str) else msg.properties  # type: ignore[arg-type]
        msg.content_blocks = [json.loads(j) if isinstance(j, str) else j for j in msg.content_blocks]  # type: ignore[arg-type]
        msg.category = msg.category or ""
        new_messages.append(msg)

    return [MessageRead.model_validate(message, from_attributes=True) for message in new_messages]