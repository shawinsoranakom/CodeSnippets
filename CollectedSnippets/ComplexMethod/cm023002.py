async def test_async_handle_intents(hass: HomeAssistant) -> None:
    """Test handling registered intents with async_handle_intents."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})

    # Reuse custom sentences in test config to trigger default agent.
    class OrderBeerIntentHandler(intent.IntentHandler):
        intent_type = "OrderBeer"

        def __init__(self) -> None:
            super().__init__()
            self.was_handled = False

        async def async_handle(
            self, intent_obj: intent.Intent
        ) -> intent.IntentResponse:
            self.was_handled = True
            return intent_obj.create_response()

    handler = OrderBeerIntentHandler()
    intent.async_register(hass, handler)

    # Registered intent will be handled
    user_input = ConversationInput(
        text="I'd like to order a stout",
        context=Context(),
        agent_id=conversation.HOME_ASSISTANT_AGENT,
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
    )
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        result = await async_handle_intents(hass, user_input, chat_log)
    assert result is not None
    assert result.intent is not None
    assert result.intent.intent_type == handler.intent_type
    assert handler.was_handled

    # No error messages, just None as a result
    user_input2 = ConversationInput(
        text="this sentence does not exist",
        agent_id=conversation.HOME_ASSISTANT_AGENT,
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
    )
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input2) as chat_log,
    ):
        result = await async_handle_intents(hass, user_input2, chat_log)
    assert result is None