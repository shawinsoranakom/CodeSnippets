async def test_eve_thermo_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test Eve Thermo."""
    # Valve position
    state = hass.states.get("sensor.eve_thermo_20ebp1701_valve_position")
    assert state
    assert state.state == "10"

    set_node_attribute(matter_node, 1, 319486977, 319422488, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.eve_thermo_20ebp1701_valve_position")
    assert state
    assert state.state == "0"

    # LocalTemperature
    state = hass.states.get("sensor.eve_thermo_20ebp1701_temperature")
    assert state
    assert state.state == "21.0"

    set_node_attribute(matter_node, 1, 513, 0, 1800)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.eve_thermo_20ebp1701_temperature")
    assert state
    assert state.state == "18.0"