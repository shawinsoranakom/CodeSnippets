def update_active_working_seconds(
    event_store: EventStore, conversation_id: str, user_id: str, file_store: FileStore
):
    """
    Calculate and update the total active working seconds for a conversation.

    This function reads all events for the conversation, looks for AgentStateChanged
    observations, and calculates the total time spent in a running state.

    Args:
        event_store: The EventStore instance for reading events
        conversation_id: The conversation ID to process
        user_id: The user ID associated with the conversation
        file_store: The FileStore instance for accessing conversation data
    """
    try:
        # Track agent state changes and calculate running time
        running_start_time = None
        total_running_seconds = 0.0

        for event in event_store.search_events():
            if isinstance(event, AgentStateChangedObservation) and event.timestamp:
                event_timestamp = datetime.fromisoformat(event.timestamp).timestamp()

                if event.agent_state == AgentState.RUNNING:
                    # Agent started running
                    if running_start_time is None:
                        running_start_time = event_timestamp
                elif running_start_time is not None:
                    # Agent stopped running, calculate duration
                    duration = event_timestamp - running_start_time
                    total_running_seconds += duration
                    running_start_time = None

        # If agent is still running at the end, don't count that time yet
        # (it will be counted when the agent stops)

        # Create or update the conversation_work record
        with session_maker() as session:
            conversation_work = (
                session.query(ConversationWork)
                .filter(ConversationWork.conversation_id == conversation_id)
                .first()
            )

            if conversation_work:
                # Update existing record
                conversation_work.seconds = total_running_seconds
                conversation_work.updated_at = datetime.now().isoformat()
            else:
                # Create new record
                conversation_work = ConversationWork(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    seconds=total_running_seconds,
                )
                session.add(conversation_work)

            session.commit()

        logger.info(
            'updated_active_working_seconds',
            extra={
                'conversation_id': conversation_id,
                'user_id': user_id,
                'total_seconds': total_running_seconds,
            },
        )

    except Exception as e:
        logger.error(
            'failed_to_update_active_working_seconds',
            extra={
                'conversation_id': conversation_id,
                'user_id': user_id,
                'error': str(e),
            },
        )