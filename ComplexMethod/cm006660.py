async def astore_message(
    message: Message,
    flow_id: str | UUID | None = None,
) -> list[Message]:
    """Store a message in the memory.

    Args:
        message (Message): The message to store.
        flow_id (Optional[str | UUID]): The flow ID associated with the message.
            When running from the CustomComponent you can access this using `self.graph.flow_id`.

    Returns:
        List[Message]: A list containing the stored message.

    Raises:
        ValueError: If any of the required parameters (session_id, sender, sender_name) is not provided.
    """
    if not message:
        logger.warning("No message provided.")
        return []

    if not message.session_id or not message.sender or not message.sender_name:
        msg = (
            f"All of session_id, sender, and sender_name must be provided. Session ID: {message.session_id},"
            f" Sender: {message.sender}, Sender Name: {message.sender_name}"
        )
        raise ValueError(msg)

    # Set flow_id if provided
    if flow_id:
        if isinstance(flow_id, str):
            flow_id = UUID(flow_id)
        message.flow_id = str(flow_id)

    # In lfx, we use the service architecture - this is a simplified implementation
    # that doesn't persist to database but maintains the message in memory
    # Real implementation would require a database service
    async with session_scope() as session:
        # Since we're using NoopSession by default, this doesn't actually persist
        # but maintains the same interface as langflow.memory
        try:
            # Generate an ID if not present
            if not hasattr(message, "id") or not message.id:
                try:
                    import nanoid

                    message.id = nanoid.generate()
                except ImportError:
                    # Fallback to uuid if nanoid is not available
                    import uuid

                    message.id = str(uuid.uuid4())

            await session.add(message)
            await session.commit()
            logger.debug(f"Message stored with ID: {message.id}")
        except Exception as e:
            logger.exception(f"Error storing message: {e}")
            await session.rollback()
            raise
        return [message]