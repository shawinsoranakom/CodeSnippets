async def test_pump(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test pump sensors."""
    # PumpStatus
    state = hass.states.get("binary_sensor.mock_pump_running")
    assert state
    assert state.state == "on"

    set_node_attribute(matter_node, 1, 512, 16, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_pump_running")
    assert state
    assert state.state == "off"

    # Initial state: kRunning bit only (no fault bits) should be off
    state = hass.states.get("binary_sensor.mock_pump_problem")
    assert state
    assert state.state == "off"

    # Set DeviceFault bit
    set_node_attribute(matter_node, 1, 512, 16, 1)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_pump_problem")
    assert state
    assert state.state == "on"

    # Clear all bits - problem sensor should be off
    set_node_attribute(matter_node, 1, 512, 16, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("binary_sensor.mock_pump_problem")
    assert state
    assert state.state == "off"

    # Set SupplyFault bit
    set_node_attribute(matter_node, 1, 512, 16, 2)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_pump_problem")
    assert state
    assert state.state == "on"