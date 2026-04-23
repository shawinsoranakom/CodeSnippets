async def test_thermostat_humidity(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test thermostat humidity attribute and state updates."""
    # test entity attributes
    state = hass.states.get("climate.longan_link_hvac")
    assert state

    measured_value = clusters.RelativeHumidityMeasurement.Attributes.MeasuredValue

    # test current humidity update from device
    set_node_attribute(
        matter_node,
        1,
        measured_value.cluster_id,
        measured_value.attribute_id,
        1234,
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.longan_link_hvac")
    assert state
    assert state.attributes["current_humidity"] == 12.34

    # test current humidity update from device with zero value
    set_node_attribute(
        matter_node,
        1,
        measured_value.cluster_id,
        measured_value.attribute_id,
        0,
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.longan_link_hvac")
    assert state
    assert state.attributes["current_humidity"] == 0.0

    # test current humidity update from device with None value
    set_node_attribute(
        matter_node,
        1,
        measured_value.cluster_id,
        measured_value.attribute_id,
        None,
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.longan_link_hvac")
    assert state
    assert "current_humidity" not in state.attributes