async def aupdate_messages(messages: Message | list[Message]) -> list[Message]:
    """Update stored messages.

    Args:
        messages: Message or list of messages to update.

    Returns:
        List[Message]: Updated messages.

    Raises:
        ValueError: If message is not found for update.
    """
    if not isinstance(messages, list):
        messages = [messages]

    async with session_scope() as session:
        updated_messages: list[Message] = []
        for message in messages:
            try:
                # In a real implementation, this would update the database record
                # For now, we just validate the message has an ID and return it
                if not hasattr(message, "id") or not message.id:
                    error_message = f"Message without ID cannot be updated: {message}"
                    logger.warning(error_message)
                    raise ValueError(error_message)

                # Convert flow_id to string if it's a UUID
                if message.flow_id and isinstance(message.flow_id, UUID):
                    message.flow_id = str(message.flow_id)

                await session.add(message)
                await session.commit()
                await session.refresh(message)
                updated_messages.append(message)
                logger.debug(f"Message updated: {message.id}")
            except Exception as e:
                logger.exception(f"Error updating message: {e}")
                await session.rollback()
                msg = f"Failed to update message: {e}"
                logger.error(msg)
                raise ValueError(msg) from e

        return updated_messages