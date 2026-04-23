async def test_intent_set_humidity_and_turn_on(hass: HomeAssistant) -> None:
    """Test the set humidity intent for turned off humidifier."""
    assert await async_setup_component(hass, "homeassistant", {})
    hass.states.async_set(
        "humidifier.bedroom_humidifier", STATE_OFF, {ATTR_HUMIDITY: 40}
    )
    humidity_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)
    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    await intent.async_setup_intents(hass)

    result = await async_handle(
        hass,
        "test",
        intent.INTENT_HUMIDITY,
        {"name": {"value": "Bedroom humidifier"}, "humidity": {"value": "50"}},
        assistant=conversation.DOMAIN,
    )
    await hass.async_block_till_done()

    assert (
        result.speech["plain"]["speech"]
        == "Turned bedroom humidifier on and set humidity to 50%"
    )

    assert len(turn_on_calls) == 1
    call = turn_on_calls[0]
    assert call.domain == DOMAIN
    assert call.service == SERVICE_TURN_ON
    assert call.data.get(ATTR_ENTITY_ID) == "humidifier.bedroom_humidifier"
    assert len(humidity_calls) == 1
    call = humidity_calls[0]
    assert call.domain == DOMAIN
    assert call.service == SERVICE_SET_HUMIDITY
    assert call.data.get(ATTR_ENTITY_ID) == "humidifier.bedroom_humidifier"
    assert call.data.get(ATTR_HUMIDITY) == 50