async def test_list_select_entities(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test ListSelect entities are discovered and working from a laundrywasher fixture."""
    state = hass.states.get("select.laundrywasher_temperature_level")
    assert state
    assert state.state == "Colors"
    assert state.attributes["options"] == ["Cold", "Colors", "Whites"]
    # Change temperature_level
    set_node_attribute(matter_node, 1, 86, 4, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("select.laundrywasher_temperature_level")
    assert state.state == "Cold"
    # test select option
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.laundrywasher_temperature_level",
            "option": "Whites",
        },
        blocking=True,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.TemperatureControl.Commands.SetTemperature(
            targetTemperatureLevel=2
        ),
    )
    # test that an invalid value (e.g. 253) leads to an unknown state
    set_node_attribute(matter_node, 1, 86, 4, 253)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("select.laundrywasher_temperature_level")
    assert state.state == "unknown"

    # SpinSpeedCurrent
    matter_client.write_attribute.reset_mock()
    state = hass.states.get("select.laundrywasher_spin_speed")
    assert state
    assert state.state == "Off"
    assert state.attributes["options"] == ["Off", "Low", "Medium", "High"]
    set_node_attribute(matter_node, 1, 83, 1, 3)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("select.laundrywasher_spin_speed")
    assert state.state == "High"
    # test select option
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.laundrywasher_spin_speed",
            "option": "High",
        },
        blocking=True,
    )
    assert matter_client.write_attribute.call_count == 1
    assert matter_client.write_attribute.call_args == call(
        node_id=matter_node.node_id,
        attribute_path=create_attribute_path_from_attribute(
            endpoint_id=1,
            attribute=clusters.LaundryWasherControls.Attributes.SpinSpeedCurrent,
        ),
        value=3,
    )
    # test that an invalid value (e.g. 253) leads to an unknown state
    set_node_attribute(matter_node, 1, 83, 1, 253)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("select.laundrywasher_spin_speed")
    assert state.state == "unknown"