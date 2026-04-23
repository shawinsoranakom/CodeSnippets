async def test_smoke_detector(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test smoke detector sensor."""
    smoke_state_attribute = clusters.SmokeCoAlarm.Attributes.SmokeState

    # Test initial state (SmokeState = 0, kNormal)
    state = hass.states.get("binary_sensor.smoke_sensor_smoke")
    assert state
    assert state.state == "off"

    # Set SmokeState to kWarning (value 1)
    set_node_attribute(
        matter_node,
        1,
        smoke_state_attribute.cluster_id,
        smoke_state_attribute.attribute_id,
        1,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smoke_sensor_smoke")
    assert state
    assert state.state == "on"

    # Set SmokeState to kCritical (value 2)
    set_node_attribute(
        matter_node,
        1,
        smoke_state_attribute.cluster_id,
        smoke_state_attribute.attribute_id,
        2,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smoke_sensor_smoke")
    assert state
    assert state.state == "on"

    # Set SmokeState back to kNormal (value 0)
    set_node_attribute(
        matter_node,
        1,
        smoke_state_attribute.cluster_id,
        smoke_state_attribute.attribute_id,
        0,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("binary_sensor.smoke_sensor_smoke")
    assert state
    assert state.state == "off"