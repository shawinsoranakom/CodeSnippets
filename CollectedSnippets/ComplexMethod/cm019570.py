async def test_co_detector(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test CO detector sensor."""
    co_state_attribute = clusters.SmokeCoAlarm.Attributes.COState

    # Test initial state (COState = 0, kNormal)
    state = hass.states.get("binary_sensor.smart_co_sensor_carbon_monoxide")
    assert state
    assert state.state == "off"

    # Set COState to kWarning (value 1)
    set_node_attribute(
        matter_node,
        1,
        co_state_attribute.cluster_id,
        co_state_attribute.attribute_id,
        1,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smart_co_sensor_carbon_monoxide")
    assert state
    assert state.state == "on"

    # Set COState to kCritical (value 2)
    set_node_attribute(
        matter_node,
        1,
        co_state_attribute.cluster_id,
        co_state_attribute.attribute_id,
        2,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smart_co_sensor_carbon_monoxide")
    assert state
    assert state.state == "on"

    # Set COState back to kNormal (value 0)
    set_node_attribute(
        matter_node,
        1,
        co_state_attribute.cluster_id,
        co_state_attribute.attribute_id,
        0,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smart_co_sensor_carbon_monoxide")
    assert state
    assert state.state == "off"