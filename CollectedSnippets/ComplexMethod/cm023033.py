async def test_handle_intents_filters_results(
    hass: HomeAssistant,
    init_components: None,
    area_registry: ar.AreaRegistry,
) -> None:
    """Test that handle_intents can filter responses."""
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

    mock_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={},
        entities_list=[],
    )
    results = []

    def _filter_intents(result):
        results.append(result)
        # We filter first, not 2nd.
        return len(results) == 1

    with (
        patch(
            "homeassistant.components.conversation.default_agent.DefaultAgent.async_recognize_intent",
            return_value=mock_result,
        ) as mock_recognize,
        patch(
            "homeassistant.components.conversation.default_agent.DefaultAgent._async_process_intent_result",
        ) as mock_process,
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await agent.async_handle_intents(
            user_input, chat_log, intent_filter=_filter_intents
        )

        assert len(mock_recognize.mock_calls) == 1
        assert len(mock_process.mock_calls) == 0

        # It was ignored
        assert response is None

        # Check we filtered things
        assert len(results) == 1
        assert results[0] is mock_result

        # Second time it is not filtered
        response = await agent.async_handle_intents(
            user_input, chat_log, intent_filter=_filter_intents
        )

        assert len(mock_recognize.mock_calls) == 2
        assert len(mock_process.mock_calls) == 2

        # Check we filtered things
        assert len(results) == 2
        assert results[1] is mock_result

        # It was ignored
        assert response is not None