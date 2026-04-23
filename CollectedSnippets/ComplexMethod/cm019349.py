async def test_get_weather(hass: HomeAssistant) -> None:
    """Test get weather for first entity and by name."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "weather", {"weather": {}})

    entity1 = WeatherEntity()
    entity1._attr_name = "Weather 1"
    entity1.entity_id = "weather.test_1"
    async_expose_entity(hass, conversation.DOMAIN, entity1.entity_id, True)

    entity2 = WeatherEntity()
    entity2._attr_name = "Weather 2"
    entity2.entity_id = "weather.test_2"
    async_expose_entity(hass, conversation.DOMAIN, entity2.entity_id, True)

    await hass.data[DOMAIN].async_add_entities([entity1, entity2])

    await weather_intent.async_setup_intents(hass)

    # First entity will be chosen
    response = await intent.async_handle(
        hass, "test", weather_intent.INTENT_GET_WEATHER, {}
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    state = response.matched_states[0]
    assert state.entity_id == entity1.entity_id

    # Named entity will be chosen
    response = await intent.async_handle(
        hass,
        "test",
        weather_intent.INTENT_GET_WEATHER,
        {"name": {"value": "Weather 2"}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    state = response.matched_states[0]
    assert state.entity_id == entity2.entity_id

    # Should fail if not exposed
    async_expose_entity(hass, conversation.DOMAIN, entity1.entity_id, False)
    async_expose_entity(hass, conversation.DOMAIN, entity2.entity_id, False)
    for name in (entity1.name, entity2.name):
        with pytest.raises(intent.MatchFailedError) as err:
            await intent.async_handle(
                hass,
                "test",
                weather_intent.INTENT_GET_WEATHER,
                {"name": {"value": name}},
                assistant=conversation.DOMAIN,
            )
        assert err.value.result.no_match_reason == intent.MatchFailedReason.ASSISTANT