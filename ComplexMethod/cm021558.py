async def test_restore_state_and_return_to_normal(hass: HomeAssistant) -> None:
    """Ensure retain of target humidity for normal mode."""
    _setup_sensor(hass, 55)
    await hass.async_block_till_done()
    mock_restore_cache(
        hass,
        (
            State(
                "humidifier.test_hygrostat",
                STATE_OFF,
                {
                    ATTR_ENTITY_ID: ENTITY,
                    ATTR_HUMIDITY: "40",
                    ATTR_MODE: MODE_AWAY,
                    ATTR_SAVED_HUMIDITY: "50",
                },
            ),
        ),
    )

    hass.set_state(CoreState.starting)

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
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_HUMIDITY] == 40
    assert state.attributes[ATTR_SAVED_HUMIDITY] == 50
    assert state.attributes[ATTR_MODE] == MODE_AWAY
    assert state.state == STATE_OFF

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_ENTITY_ID: "humidifier.test_hygrostat", ATTR_MODE: MODE_NORMAL},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("humidifier.test_hygrostat")
    assert state.attributes[ATTR_HUMIDITY] == 50
    assert state.attributes[ATTR_MODE] == MODE_NORMAL
    assert state.state == STATE_OFF