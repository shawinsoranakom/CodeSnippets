async def test_water_valve(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test valve alarms."""
    # ValveFault default state
    state = hass.states.get("binary_sensor.mock_valve_general_fault")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_blocked")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_leaking")
    assert state
    assert state.state == "off"

    # ValveFault general_fault test (bit 0)
    set_node_attribute(matter_node, 1, 129, 9, 1)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_valve_general_fault")
    assert state
    assert state.state == "on"

    state = hass.states.get("binary_sensor.mock_valve_valve_blocked")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_leaking")
    assert state
    assert state.state == "off"

    # ValveFault valve_blocked test (bit 1)
    set_node_attribute(matter_node, 1, 129, 9, 2)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_valve_general_fault")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_blocked")
    assert state
    assert state.state == "on"

    state = hass.states.get("binary_sensor.mock_valve_valve_leaking")
    assert state
    assert state.state == "off"

    # ValveFault valve_leaking test (bit 2)
    set_node_attribute(matter_node, 1, 129, 9, 4)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_valve_general_fault")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_blocked")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_leaking")
    assert state
    assert state.state == "on"

    # ValveFault multiple faults test (bits 0 and 2)
    set_node_attribute(matter_node, 1, 129, 9, 5)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.mock_valve_general_fault")
    assert state
    assert state.state == "on"

    state = hass.states.get("binary_sensor.mock_valve_valve_blocked")
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_valve_valve_leaking")
    assert state
    assert state.state == "on"