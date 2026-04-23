async def test_light_turn_on_off(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
    entity_id: str,
    supported_color_modes: list[str],
) -> None:
    """Test basic light discovery and turn on/off."""

    # Test that the light is off
    set_node_attribute(matter_node, 1, 6, 0, False)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"

    # check the supported_color_modes
    # especially important is the onoff light device type that does have
    # a levelcontrol cluster present which we should ignore
    assert state.attributes["supported_color_modes"] == supported_color_modes

    # Test that the light is on
    set_node_attribute(matter_node, 1, 6, 0, True)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"

    # Turn the light off
    await hass.services.async_call(
        "light",
        "turn_off",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.OnOff.Commands.Off(),
    )
    matter_client.send_device_command.reset_mock()

    # Turn the light on
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.OnOff.Commands.On(),
    )
    matter_client.send_device_command.reset_mock()