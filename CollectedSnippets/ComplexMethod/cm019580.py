async def test_attribute_select_entities(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test select entities are created for attribute based discovery schema(s)."""
    entity_id = "select.mock_dimmable_light_power_on_behavior"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "previous"
    assert state.attributes["options"] == ["on", "off", "toggle", "previous"]
    assert state.attributes["friendly_name"] == "Mock Dimmable Light Power-on behavior"
    set_node_attribute(matter_node, 1, 6, 16387, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.state == "on"
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": entity_id,
            "option": "off",
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.OnOff.Attributes.StartUpOnOff,
        ),
        value=0,
    )
    # test that an invalid value (e.g. 253) leads to an unknown state
    set_node_attribute(matter_node, 1, 6, 16387, 253)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.state == "unknown"