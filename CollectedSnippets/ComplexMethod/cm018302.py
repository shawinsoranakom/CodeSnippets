async def test_battery_sensor(
    hass: HomeAssistant,
    command_store: CommandStore,
    device: Device,
) -> None:
    """Test that a battery sensor is correctly added."""
    entity_id = "sensor.test_battery"
    await setup_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "87"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.BATTERY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    await command_store.trigger_observe_callback(
        hass, device, {ATTR_DEVICE_INFO: {ATTR_DEVICE_BATTERY: 60}}
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "60"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.BATTERY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT