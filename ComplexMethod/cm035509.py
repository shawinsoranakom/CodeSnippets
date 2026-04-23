async def auto_generate_title(
    conversation_id: str,
    user_id: str | None,
    file_store: FileStore,
    settings: Settings,
    llm_registry: LLMRegistry,
) -> str:
    """Auto-generate a title for a conversation based on the first user message.
    Uses LLM-based title generation if available, otherwise falls back to a simple truncation.

    Args:
        conversation_id: The ID of the conversation
        user_id: The ID of the user

    Returns:
        A generated title string
    """
    try:
        # Create an event store for the conversation
        event_store = EventStore(conversation_id, file_store, user_id)

        # Find the first user message
        first_user_message = None
        for event in event_store.search_events():
            if (
                event.source == EventSource.USER
                and isinstance(event, MessageAction)
                and event.content
                and event.content.strip()
            ):
                first_user_message = event.content
                break

        if first_user_message:
            # Get LLM config from user settings
            try:
                if settings:
                    agent_settings = settings.agent_settings
                    settings_base_url = agent_settings.llm.base_url
                    effective_base_url = get_effective_llm_base_url(
                        agent_settings.llm.model,
                        settings_base_url,
                    )
                    raw_api_key = settings.agent_settings.llm.api_key
                    api_key = (
                        SecretStr(raw_api_key)
                        if isinstance(raw_api_key, str)
                        else raw_api_key
                    )
                    llm_config = LLMConfig(
                        model=agent_settings.llm.model,
                        api_key=api_key,
                        base_url=effective_base_url,
                    )

                    # Try to generate title using LLM
                    llm_title = await generate_conversation_title(
                        first_user_message, llm_config, llm_registry
                    )
                    if llm_title:
                        logger.info(f'Generated title using LLM: {llm_title}')
                        return llm_title
            except Exception as e:
                logger.error(f'Error using LLM for title generation: {e}')

            # Fall back to simple truncation if LLM generation fails or is unavailable
            first_user_message = first_user_message.strip()
            title = first_user_message[:30]
            if len(first_user_message) > 30:
                title += '...'
            logger.info(f'Generated title using truncation: {title}')
            return title
    except Exception as e:
        logger.error(f'Error generating title: {str(e)}')
    return ''