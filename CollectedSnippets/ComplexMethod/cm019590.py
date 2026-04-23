async def test_occupancy_sensing_pir_attributes(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test PIR occupancy sensor attributes."""
    # PIRUnoccupiedToOccupiedDelay
    state = hass.states.get("number.mock_pir_occupancy_sensor_detection_delay")
    assert state
    assert state.state == "10"
    assert state.attributes["min"] == 0
    assert state.attributes["max"] == 65534
    assert state.attributes["unit_of_measurement"] == "s"

    set_node_attribute(matter_node, 1, 1030, 17, 20)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("number.mock_pir_occupancy_sensor_detection_delay")
    assert state
    assert state.state == "20"

    # PIRUnoccupiedToOccupiedThreshold
    state = hass.states.get("number.mock_pir_occupancy_sensor_detection_threshold")
    assert state
    assert state.state == "1"
    assert state.attributes["min"] == 1
    assert state.attributes["max"] == 254

    set_node_attribute(matter_node, 1, 1030, 18, 5)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("number.mock_pir_occupancy_sensor_detection_threshold")
    assert state
    assert state.state == "5"

    # Test set value for delay
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.mock_pir_occupancy_sensor_detection_delay",
            "value": 15,
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.OccupancySensing.Attributes.PIRUnoccupiedToOccupiedDelay,
        ),
        value=15,
    )

    # Test set value for threshold
    matter_client.write_attribute.reset_mock()
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.mock_pir_occupancy_sensor_detection_threshold",
            "value": 3,
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.OccupancySensing.Attributes.PIRUnoccupiedToOccupiedThreshold,
        ),
        value=3,
    )