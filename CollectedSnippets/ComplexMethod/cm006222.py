async def aupdate_messages(messages: Message | list[Message]) -> list[Message]:
    if not isinstance(messages, list):
        messages = [messages]

    async with session_scope() as session:
        updated_messages: list[MessageTable] = []
        for message in messages:
            msg = await session.get(MessageTable, message.id)
            if msg:
                msg = msg.sqlmodel_update(message.model_dump(exclude_unset=True, exclude_none=True))
                # Convert flow_id to UUID if it's a string preventing error when saving to database
                if msg.flow_id and isinstance(msg.flow_id, str):
                    msg.flow_id = UUID(msg.flow_id)
                result = session.add(msg)
                if asyncio.iscoroutine(result):
                    await result
                updated_messages.append(msg)
            else:
                error_message = f"Message with id {message.id} not found"
                await logger.awarning(error_message)
                raise ValueError(error_message)

        return [MessageRead.model_validate(message, from_attributes=True) for message in updated_messages]