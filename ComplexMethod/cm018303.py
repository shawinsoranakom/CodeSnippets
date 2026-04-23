async def test_air_quality_sensor(
    hass: HomeAssistant,
    command_store: CommandStore,
    device: Device,
) -> None:
    """Test that a battery sensor is correctly added."""
    entity_id = "sensor.test_air_quality"
    await setup_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "5"
    assert (
        state.attributes[ATTR_UNIT_OF_MEASUREMENT]
        == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert ATTR_DEVICE_CLASS not in state.attributes

    # The sensor returns 65535 if the fan is turned off
    await command_store.trigger_observe_callback(
        hass,
        device,
        {ROOT_AIR_PURIFIER: [{ATTR_AIR_PURIFIER_AIR_QUALITY: 65535}]},
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN