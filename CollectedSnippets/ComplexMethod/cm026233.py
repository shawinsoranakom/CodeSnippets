async def _call_service(
    service: ServiceCall, notify_service: TelegramNotificationService, chat_id: int
) -> dict[str, JsonValueType] | None:
    """Calls a Telegram bot service using the specified bot and chat_id."""

    service_name = service.service

    kwargs = dict(service.data)
    kwargs[ATTR_CHAT_ID] = chat_id

    messages: dict[str, JsonValueType] | None = None
    if service_name == SERVICE_SEND_MESSAGE:
        messages = await notify_service.send_message(context=service.context, **kwargs)
    elif service_name == SERVICE_SEND_MEDIA_GROUP:
        messages = await notify_service.send_media_group(
            context=service.context, **kwargs
        )
    elif service_name == SERVICE_SEND_CHAT_ACTION:
        messages = await notify_service.send_chat_action(
            context=service.context, **kwargs
        )
    elif service_name in [
        SERVICE_SEND_PHOTO,
        SERVICE_SEND_ANIMATION,
        SERVICE_SEND_VIDEO,
        SERVICE_SEND_VOICE,
        SERVICE_SEND_DOCUMENT,
    ]:
        messages = await notify_service.send_file(
            service_name, context=service.context, **kwargs
        )
    elif service_name == SERVICE_SEND_STICKER:
        messages = await notify_service.send_sticker(context=service.context, **kwargs)
    elif service_name == SERVICE_SEND_LOCATION:
        messages = await notify_service.send_location(context=service.context, **kwargs)
    elif service_name == SERVICE_SEND_POLL:
        messages = await notify_service.send_poll(context=service.context, **kwargs)
    elif service_name == SERVICE_ANSWER_CALLBACK_QUERY:
        await notify_service.answer_callback_query(context=service.context, **kwargs)
    elif service_name == SERVICE_DELETE_MESSAGE:
        await notify_service.delete_message(context=service.context, **kwargs)
    elif service_name == SERVICE_LEAVE_CHAT:
        await notify_service.leave_chat(context=service.context, **kwargs)
    elif service_name == SERVICE_SET_MESSAGE_REACTION:
        await notify_service.set_message_reaction(context=service.context, **kwargs)
    elif service_name == SERVICE_EDIT_MESSAGE_MEDIA:
        await notify_service.edit_message_media(context=service.context, **kwargs)
    elif service_name == SERVICE_SEND_MESSAGE_DRAFT:
        await notify_service.send_message_draft(context=service.context, **kwargs)
    elif service_name == SERVICE_DOWNLOAD_FILE:
        return await notify_service.download_file(context=service.context, **kwargs)
    else:
        await notify_service.edit_message(
            service_name, context=service.context, **kwargs
        )

    if service.return_response and messages is not None:
        return messages

    return None