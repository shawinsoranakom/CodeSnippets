async def test_numeric_switch(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test numeric switch entity is discovered and working using an Eve Thermo fixture ."""
    state = hass.states.get("switch.eve_thermo_20ebp1701_child_lock")
    assert state
    assert state.state == "off"
    # name should be derived from description attribute
    assert state.attributes["friendly_name"] == "Eve Thermo 20EBP1701 Child lock"
    # test attribute changes
    set_node_attribute(matter_node, 1, 516, 1, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("switch.eve_thermo_20ebp1701_child_lock")
    assert state.state == "on"
    set_node_attribute(matter_node, 1, 516, 1, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("switch.eve_thermo_20ebp1701_child_lock")
    assert state.state == "off"
    # test switch service
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.eve_thermo_20ebp1701_child_lock"},
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.ThermostatUserInterfaceConfiguration.Attributes.KeypadLockout,
        ),
        value=1,
    )
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.eve_thermo_20ebp1701_child_lock"},
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 2
    assert matter_client.write_attribute.call_args_list[1] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.ThermostatUserInterfaceConfiguration.Attributes.KeypadLockout,
        ),
        value=0,
    )