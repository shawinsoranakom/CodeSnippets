async def test_rgbww_light(hass: HomeAssistant) -> None:
    """Test a light operation with a rgbww light."""
    bulb, _ = await async_setup_integration(hass, bulb_type=FAKE_RGBWW_BULB)
    entity_id = "light.mock_title"
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBWW_COLOR: (1, 2, 3, 4, 5)},
        blocking=True,
    )
    pilot: PilotBuilder = bulb.turn_on.mock_calls[0][1][0]
    assert pilot.pilot_params == {"b": 3, "c": 4, "g": 2, "r": 1, "w": 5}

    await async_push_update(
        hass, bulb, {"mac": FAKE_MAC, "state": True, **pilot.pilot_params}
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_RGBWW_COLOR] == (1, 2, 3, 4, 5)

    bulb.turn_on.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 6535, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    pilot: PilotBuilder = bulb.turn_on.mock_calls[0][1][0]
    assert pilot.pilot_params == {"dimming": 50, "temp": 6535}
    await async_push_update(
        hass, bulb, {"mac": FAKE_MAC, "state": True, **pilot.pilot_params}
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 6535

    bulb.turn_on.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Ocean", ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    pilot: PilotBuilder = bulb.turn_on.mock_calls[0][1][0]
    assert pilot.pilot_params == {"dimming": 50, "sceneId": 1}
    await async_push_update(
        hass, bulb, {"mac": FAKE_MAC, "state": True, **pilot.pilot_params}
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "Ocean"
    assert state.attributes[ATTR_COLOR_MODE] == "brightness"

    bulb.turn_on.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Forest"},
        blocking=True,
    )
    pilot: PilotBuilder = bulb.turn_on.mock_calls[0][1][0]
    assert pilot.pilot_params == {"sceneId": 7}
    await async_push_update(
        hass, bulb, {"mac": FAKE_MAC, "state": True, **pilot.pilot_params}
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "Forest"
    assert state.attributes[ATTR_COLOR_MODE] == "onoff"

    bulb.turn_on.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Rhythm"},
        blocking=True,
    )
    pilot: PilotBuilder = bulb.turn_on.mock_calls[0][1][0]
    assert pilot.pilot_params == {}