async def test_fan_turn_on_with_preset_mode(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test turning on the fan with a specific preset mode."""
    entity_id = "fan.mocked_fan_switch"
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "medium"},
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path="1/514/0",
        value=2,
    )
    # test again with wind feature as preset mode
    for preset_mode, value in (("natural_wind", 2), ("sleep_wind", 1)):
        matter_client.write_attribute.reset_mock()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: preset_mode},
            blocking=True,
        )
        assert matter_client.write_attribute.call_count == 1
        assert matter_client.write_attribute.call_args == call(
            node_id=matter_node.node_id,
            attribute_path="1/514/10",
            value=value,
        )
    # test again if wind mode is explicitly turned off when we set a new preset mode
    matter_client.write_attribute.reset_mock()
    set_node_attribute(matter_node, 1, 514, 10, 2)
    await trigger_subscription_callback(hass, matter_client)
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "medium"},
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 2
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path="1/514/10",
        value=0,
    )
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path="1/514/0",
        value=2,
    )
    # test again where preset_mode is omitted in the service call
    # which should select the last active preset
    matter_client.write_attribute.reset_mock()
    set_node_attribute(matter_node, 1, 514, 0, 1)
    set_node_attribute(matter_node, 1, 514, 10, 0)
    await trigger_subscription_callback(hass, matter_client)
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path="1/514/0",
        value=1,
    )