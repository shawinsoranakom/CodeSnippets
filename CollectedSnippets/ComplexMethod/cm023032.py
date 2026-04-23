async def test_handle_failed_intents(
    hass: HomeAssistant,
    init_components: None,
    area_registry: ar.AreaRegistry,
    side_effect: intent.IntentError,
    error_code: intent.IntentResponseErrorCode,
    return_response: bool,
) -> None:
    """Test that error results from intent handler are saved to chat_log."""
    assert await async_setup_component(hass, "climate", {})
    area_registry.async_create("living room")

    agent = async_get_agent(hass)

    user_input = ConversationInput(
        text="What is the temperature in the living room?",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with (
        patch(
            "homeassistant.components.conversation.default_agent.intent.async_handle",
            side_effect=side_effect,
        ) as mock_handle,
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await agent.async_handle_intents(user_input, chat_log)
        assert len(chat_log.content) == 4  # System + user + tool call + tool results
        assert chat_log.content[-1].role == "tool_result"

    assert len(mock_handle.mock_calls) == 1

    if return_response:
        assert response is not None and response.error_code == error_code
    else:
        assert response is None