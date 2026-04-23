async def test_restore_will_turn_off_when_loaded_second(hass: HomeAssistant) -> None:
    """Ensure that restored state is coherent with real situation.

    Switch is not available until after component is loaded
    """
    heater_switch = "input_boolean.test"
    mock_restore_cache(
        hass,
        (
            State(
                "climate.test_thermostat",
                HVACMode.HEAT,
                {ATTR_TEMPERATURE: "18", ATTR_PRESET_MODE: PRESET_NONE},
            ),
            State(heater_switch, STATE_ON, {}),
        ),
    )

    hass.set_state(CoreState.starting)

    await hass.async_block_till_done()
    assert hass.states.get(heater_switch) is None

    _setup_sensor(hass, 16)

    await async_setup_component(
        hass,
        CLIMATE_DOMAIN,
        {
            "climate": {
                "platform": "generic_thermostat",
                "name": "test_thermostat",
                "heater": heater_switch,
                "target_sensor": ENT_SENSOR,
                "target_temp": 20,
                "initial_hvac_mode": HVACMode.OFF,
            }
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get("climate.test_thermostat")
    assert state.attributes[ATTR_TEMPERATURE] == 20
    assert state.state == HVACMode.OFF

    calls_on = async_mock_service(hass, ha.DOMAIN, SERVICE_TURN_ON)
    calls_off = async_mock_service(hass, ha.DOMAIN, SERVICE_TURN_OFF)

    assert await async_setup_component(
        hass, input_boolean.DOMAIN, {"input_boolean": {"test": None}}
    )
    await hass.async_block_till_done()
    # heater must be switched off
    assert len(calls_on) == 0
    assert len(calls_off) == 1
    call = calls_off[0]
    assert call.domain == HOMEASSISTANT_DOMAIN
    assert call.service == SERVICE_TURN_OFF
    assert call.data["entity_id"] == "input_boolean.test"