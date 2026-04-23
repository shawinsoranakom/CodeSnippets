def async_get_chat_log(
    hass: HomeAssistant,
    session: chat_session.ChatSession,
    user_input: ConversationInput | None = None,
    *,
    chat_log_delta_listener: Callable[[ChatLog, dict], None] | None = None,
) -> Generator[ChatLog]:
    """Return chat log for a specific chat session."""
    # If a chat log is already active and it's the requested conversation ID,
    # return that. We won't update the last updated time in this case.
    if (
        chat_log := current_chat_log.get()
    ) and chat_log.conversation_id == session.conversation_id:
        if chat_log_delta_listener is not None:
            raise RuntimeError(
                "Cannot attach chat log delta listener unless initial caller"
            )
        if user_input is not None and (
            (content := chat_log.content[-1]).role != "user"
            or content.content != user_input.text
        ):
            chat_log.async_add_user_content(UserContent(content=user_input.text))

        yield chat_log
        return

    all_chat_logs = hass.data.get(DATA_CHAT_LOGS)
    if all_chat_logs is None:
        all_chat_logs = {}
        hass.data[DATA_CHAT_LOGS] = all_chat_logs

    is_new_log = session.conversation_id not in all_chat_logs

    if chat_log := all_chat_logs.get(session.conversation_id):
        chat_log = replace(chat_log, content=chat_log.content.copy())
    else:
        chat_log = ChatLog(hass, session.conversation_id)

    if chat_log_delta_listener:
        chat_log.delta_listener = chat_log_delta_listener

    # Fire CREATED event for new chat logs before any content is added
    if is_new_log:
        _async_notify_subscribers(
            hass,
            session.conversation_id,
            ChatLogEventType.CREATED,
            {"chat_log": chat_log.as_dict()},
        )

    if user_input is not None:
        chat_log.async_add_user_content(UserContent(content=user_input.text))

    last_message = chat_log.content[-1]

    token = current_chat_log.set(chat_log)
    yield chat_log
    current_chat_log.reset(token)

    if chat_log.content[-1] is last_message:
        LOGGER.debug(
            "Chat Log opened but no assistant message was added, ignoring update"
        )
        # If this was a new log but nothing was added, fire DELETED to clean up
        if is_new_log:
            _async_notify_subscribers(
                hass,
                session.conversation_id,
                ChatLogEventType.DELETED,
                {},
            )
        return

    if is_new_log:

        @callback
        def do_cleanup() -> None:
            """Handle cleanup."""
            all_chat_logs.pop(session.conversation_id)
            _async_notify_subscribers(
                hass,
                session.conversation_id,
                ChatLogEventType.DELETED,
                {},
            )

        session.async_on_cleanup(do_cleanup)

    if chat_log_delta_listener:
        chat_log.delta_listener = None

    all_chat_logs[session.conversation_id] = chat_log

    # For new logs, CREATED was already fired before content was added
    # For existing logs, fire UPDATED
    if not is_new_log:
        _async_notify_subscribers(
            hass,
            session.conversation_id,
            ChatLogEventType.UPDATED,
            {"chat_log": chat_log.as_dict()},
        )