async def test_airzone_create_binary_sensors(hass: HomeAssistant) -> None:
    """Test creation of binary sensors."""

    await async_init_integration(hass)

    # Aidoo
    state = hass.states.get("binary_sensor.bron_problem")
    assert state.state == STATE_OFF
    assert state.attributes.get("errors") is None
    assert state.attributes.get("warnings") is None

    state = hass.states.get("binary_sensor.bron_running")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.bron_pro_problem")
    assert state.state == STATE_OFF
    assert state.attributes.get("errors") is None
    assert state.attributes.get("warnings") is None

    state = hass.states.get("binary_sensor.bron_pro_running")
    assert state.state == STATE_ON

    # Systems
    state = hass.states.get("binary_sensor.system_1_problem")
    assert state.state == STATE_ON
    assert state.attributes.get("errors") == [
        {
            API_OLD_ID: "error-id",
        },
    ]
    assert state.attributes.get("warnings") is None

    # Zones
    state = hass.states.get("binary_sensor.dormitorio_air_demand")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.dormitorio_air_quality_active")
    assert state is None

    state = hass.states.get("binary_sensor.dormitorio_battery")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.dormitorio_floor_demand")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.dormitorio_problem")
    assert state.state == STATE_OFF
    assert state.attributes.get("warnings") is None

    state = hass.states.get("binary_sensor.dormitorio_running")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.salon_air_demand")
    assert state.state == STATE_ON

    state = hass.states.get("binary_sensor.salon_air_quality_active")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.salon_floor_demand")
    assert state.state == STATE_OFF

    state = hass.states.get("binary_sensor.salon_problem")
    assert state.state == STATE_OFF
    assert state.attributes.get("warnings") is None

    state = hass.states.get("binary_sensor.salon_running")
    assert state.state == STATE_ON