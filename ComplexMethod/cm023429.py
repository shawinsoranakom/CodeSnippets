async def test_intent_set_mode(hass: HomeAssistant) -> None:
    """Test the set mode intent."""
    assert await async_setup_component(hass, "homeassistant", {})
    hass.states.async_set(
        "humidifier.bedroom_humidifier",
        STATE_ON,
        {
            ATTR_HUMIDITY: 40,
            ATTR_SUPPORTED_FEATURES: 1,
            ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_MODE: "home",
        },
    )
    mode_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    await intent.async_setup_intents(hass)

    result = await async_handle(
        hass,
        "test",
        intent.INTENT_MODE,
        {"name": {"value": "Bedroom humidifier"}, "mode": {"value": "away"}},
        assistant=conversation.DOMAIN,
    )
    await hass.async_block_till_done()

    assert (
        result.speech["plain"]["speech"]
        == "The mode for bedroom humidifier is set to away"
    )

    assert len(turn_on_calls) == 0
    assert len(mode_calls) == 1
    call = mode_calls[0]
    assert call.domain == DOMAIN
    assert call.service == SERVICE_SET_MODE
    assert call.data.get(ATTR_ENTITY_ID) == "humidifier.bedroom_humidifier"
    assert call.data.get(ATTR_MODE) == "away"