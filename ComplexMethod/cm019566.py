async def test_dishwasher_alarm(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test dishwasher alarm sensors."""
    state = hass.states.get("binary_sensor.dishwasher_door_alarm")
    assert state

    # set DoorAlarm alarm
    set_node_attribute(matter_node, 1, 93, 2, 4)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.dishwasher_door_alarm")
    assert state
    assert state.state == "on"

    # clear DoorAlarm alarm
    set_node_attribute(matter_node, 1, 93, 2, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.dishwasher_inflow_alarm")
    assert state
    assert state.state == "off"

    # set InflowError alarm
    set_node_attribute(matter_node, 1, 93, 2, 1)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.dishwasher_inflow_alarm")
    assert state
    assert state.state == "on"