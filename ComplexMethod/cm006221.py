async def aadd_messages(messages: Message | list[Message], flow_id: str | UUID | None = None):
    """Add a message to the monitor service."""
    if not isinstance(messages, list):
        messages = [messages]

    # Check if all messages are Message instances (either from langflow or lfx)
    for message in messages:
        # Accept Message instances from both langflow and lfx packages
        is_valid_message = isinstance(message, Message) or (
            hasattr(message, "__class__") and message.__class__.__name__ in ["Message", "ErrorMessage"]
        )
        if not is_valid_message:
            types = ", ".join([str(type(msg)) for msg in messages])
            msg = f"The messages must be instances of Message. Found: {types}"
            raise ValueError(msg)

    try:
        messages_models = [MessageTable.from_message(msg, flow_id=flow_id) for msg in messages]
        async with session_scope() as session:
            messages_models = await aadd_messagetables(messages_models, session)
        return [await Message.create(**message.model_dump()) for message in messages_models]
    except Exception as e:
        await logger.aexception(e)
        raise