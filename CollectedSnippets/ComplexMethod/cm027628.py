def async_get_chat_session(
    hass: HomeAssistant,
    conversation_id: str | None = None,
) -> Generator[ChatSession]:
    """Return a chat session."""
    if session := current_session.get():
        # If a session is already active and it's the requested conversation ID,
        # return that. We won't update the last updated time in this case.
        if session.conversation_id == conversation_id:
            yield session
            return

        # If it's not the same conversation ID, we will create a new session
        # because it might be a conversation agent calling a tool that is talking
        # to another LLM.
        session = None

    all_sessions = hass.data.get(DATA_CHAT_SESSION)
    if all_sessions is None:
        all_sessions = {}
        hass.data[DATA_CHAT_SESSION] = all_sessions
        hass.data[DATA_CHAT_SESSION_CLEANUP] = SessionCleanup(hass)

    if conversation_id is None:
        conversation_id = ulid_now()

    elif conversation_id in all_sessions:
        session = all_sessions[conversation_id]

    else:
        # Conversation IDs are ULIDs. We generate a new one if not provided.
        # If an old ULID is passed in, we will generate a new one to indicate
        # a new conversation was started. If the user picks their own, they
        # want to track a conversation and we respect it.
        try:
            ulid_to_bytes(conversation_id)
            conversation_id = ulid_now()
        except ValueError:
            pass

    if session is None:
        LOGGER.debug("Creating new session %s", conversation_id)
        session = ChatSession(conversation_id)

    current_session.set(session)
    yield session
    current_session.set(None)

    session.last_updated = dt_util.utcnow()
    all_sessions[conversation_id] = session
    hass.data[DATA_CHAT_SESSION_CLEANUP].schedule()