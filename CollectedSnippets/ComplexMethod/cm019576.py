async def test_pump(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test pump sensors."""
    # ControlMode
    state = hass.states.get("sensor.mock_pump_control_mode")
    assert state
    assert state.state == "constant_temperature"

    set_node_attribute(matter_node, 1, 512, 33, 7)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_pump_control_mode")
    assert state
    assert state.state == "automatic"

    # Speed
    state = hass.states.get("sensor.mock_pump_rotation_speed")
    assert state
    assert state.state == "1000"

    set_node_attribute(matter_node, 1, 512, 20, 500)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_pump_rotation_speed")
    assert state
    assert state.state == "500"