async def test_water_heater_boostmode(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test water_heater set operation mode service."""
    # Boost 1h (3600s)
    boost_info: type[
        clusters.WaterHeaterManagement.Structs.WaterHeaterBoostInfoStruct
    ] = clusters.WaterHeaterManagement.Structs.WaterHeaterBoostInfoStruct(duration=3600)
    state = hass.states.get("water_heater.water_heater")
    assert state

    # enable water_heater boostmode
    await hass.services.async_call(
        "water_heater",
        "set_operation_mode",
        {
            "entity_id": "water_heater.water_heater",
            "operation_mode": STATE_HIGH_DEMAND,
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=2,
            attribute=clusters.Thermostat.Attributes.SystemMode,
        ),
        value=4,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=2,
        command=clusters.WaterHeaterManagement.Commands.Boost(boostInfo=boost_info),
    )

    # disable water_heater boostmode
    await hass.services.async_call(
        "water_heater",
        "set_operation_mode",
        {
            "entity_id": "water_heater.water_heater",
            "operation_mode": STATE_ECO,
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 2
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=2,
            attribute=clusters.Thermostat.Attributes.SystemMode,
        ),
        value=4,
    )
    assert matter_client.send_device_command.call_count == 2
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=2,
        command=clusters.WaterHeaterManagement.Commands.CancelBoost(),
    )