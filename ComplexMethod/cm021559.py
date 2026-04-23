async def test_away_fixed_humidity_mode(hass: HomeAssistant) -> None:
    """Ensure retain of target humidity for normal mode."""
    _setup_sensor(hass, 45)
    await hass.async_block_till_done()
    await async_setup_component(
        hass,
        HUMIDIFIER_DOMAIN,
        {
            "humidifier": {
                "platform": "generic_hygrostat",
                "name": "test_hygrostat",
                "humidifier": ENT_SWITCH,
                "target_sensor": ENT_SENSOR,
                "away_humidity": 32,
                "target_humidity": 40,
                "away_fixed": True,
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_HUMIDITY] == 40
    assert state.attributes[ATTR_MODE] == MODE_NORMAL
    assert state.state == STATE_OFF

    # Switch to Away mode
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_ENTITY_ID: "humidifier.test_hygrostat", ATTR_MODE: MODE_AWAY},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Target humidity changed to away_humidity
    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_MODE] == MODE_AWAY
    assert state.attributes[ATTR_HUMIDITY] == 32
    assert state.attributes[ATTR_SAVED_HUMIDITY] == 40
    assert state.state == STATE_OFF

    # Change target humidity
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_ENTITY_ID: "humidifier.test_hygrostat", ATTR_HUMIDITY: 42},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Current target humidity not changed
    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_HUMIDITY] == 32
    assert state.attributes[ATTR_SAVED_HUMIDITY] == 42
    assert state.attributes[ATTR_MODE] == MODE_AWAY
    assert state.state == STATE_OFF

    # Return to Normal mode
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_ENTITY_ID: "humidifier.test_hygrostat", ATTR_MODE: MODE_NORMAL},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Target humidity changed to away_humidity
    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_HUMIDITY] == 42
    assert state.attributes[ATTR_SAVED_HUMIDITY] == 32
    assert state.attributes[ATTR_MODE] == MODE_NORMAL
    assert state.state == STATE_OFF