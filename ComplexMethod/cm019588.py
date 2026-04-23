async def test_level_control_config_entities(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test number entities are created for the LevelControl cluster (config) attributes."""
    state = hass.states.get("number.mock_dimmable_light_on_level")
    assert state
    assert state.state == "255"

    state = hass.states.get("number.mock_dimmable_light_power_on_level")
    assert state
    assert state.state == "255"

    state = hass.states.get("number.mock_dimmable_light_on_transition_time")
    assert state
    assert state.state == "0.0"

    state = hass.states.get("number.mock_dimmable_light_off_transition_time")
    assert state
    assert state.state == "0.0"

    state = hass.states.get("number.mock_dimmable_light_on_off_transition_time")
    assert state
    assert state.state == "0.0"

    set_node_attribute(matter_node, 1, 0x00000008, 0x0011, 20)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("number.mock_dimmable_light_on_level")
    assert state
    assert state.state == "20"

    set_node_attribute(matter_node, 1, 0x00000008, 0x4000, 128)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("number.mock_dimmable_light_power_on_level")
    assert state
    assert state.state == "128"

    set_node_attribute(matter_node, 1, 0x00000008, 0x4000, 255)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("number.mock_dimmable_light_power_on_level")
    assert state
    assert state.state == "255"
    # Set a concrete value (not null)
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.mock_dimmable_light_power_on_level",
            "value": 128,
        },
        blocking=True,
    )

    # Verify write
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.LevelControl.Attributes.StartUpCurrentLevel,
        ),
        value=128,
    )

    matter_client.write_attribute.reset_mock()
    # Set a null-equivalent value (255 should map to None on the wire)
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.mock_dimmable_light_power_on_level",
            "value": 255,
        },
        blocking=True,
    )

    # Verify write
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args_list[0] == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.LevelControl.Attributes.StartUpCurrentLevel,
        ),
        value=None,
    )