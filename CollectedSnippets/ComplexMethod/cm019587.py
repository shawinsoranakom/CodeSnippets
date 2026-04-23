async def test_speaker_mute_uses_onoff_commands(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test speaker mute switch uses On/Off commands instead of attribute writes."""

    state = hass.states.get("switch.mock_speaker_mute")
    assert state
    assert state.state == "off"

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.mock_speaker_mute"},
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.OnOff.Commands.Off(),
    )

    set_node_attribute(matter_node, 1, 6, 0, False)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("switch.mock_speaker_mute")
    assert state
    assert state.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.mock_speaker_mute"},
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.OnOff.Commands.On(),
    )

    set_node_attribute(matter_node, 1, 6, 0, True)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("switch.mock_speaker_mute")
    assert state
    assert state.state == "off"