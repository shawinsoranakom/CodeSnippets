async def astore_message(
    message: Message,
    flow_id: str | UUID | None = None,
) -> list[Message]:
    """Stores a message in the memory.

    Args:
        message (Message): The message to store.
        flow_id (Optional[str]): The flow ID associated with the message.
            When running from the CustomComponent you can access this using `self.graph.flow_id`.

    Returns:
        List[Message]: A list of data containing the stored message.

    Raises:
        ValueError: If any of the required parameters (session_id, sender, sender_name) is not provided.
    """
    if not message:
        await logger.awarning("No message provided.")
        return []

    if not message.session_id or not message.sender or not message.sender_name:
        msg = (
            f"All of session_id, sender, and sender_name must be provided. Session ID: {message.session_id},"
            f" Sender: {message.sender}, Sender Name: {message.sender_name}"
        )
        raise ValueError(msg)
    if hasattr(message, "id") and message.id:
        # if message has an id and exist in the database, update it
        # if not raise an error and add the message to the database
        try:
            return await aupdate_messages([message])
        except ValueError as e:
            await logger.aerror(e)
    if flow_id and not isinstance(flow_id, UUID):
        flow_id = UUID(flow_id)
    return await aadd_messages([message], flow_id=flow_id)