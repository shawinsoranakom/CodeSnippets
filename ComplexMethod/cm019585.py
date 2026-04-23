async def test_extended_color_light(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
    entity_id: str,
) -> None:
    """Test an extended color light."""

    # Test that the XY color changes
    set_node_attribute(matter_node, 1, 768, 8, 1)
    set_node_attribute(matter_node, 1, 768, 3, 50)
    set_node_attribute(matter_node, 1, 768, 4, 100)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["color_mode"] == ColorMode.XY
    assert state.attributes["xy_color"] == (0.0007630, 0.001526)

    # Test that the HS color changes
    set_node_attribute(matter_node, 1, 768, 8, 0)
    set_node_attribute(matter_node, 1, 768, 1, 50)
    set_node_attribute(matter_node, 1, 768, 0, 100)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["color_mode"] == ColorMode.HS
    assert state.attributes["hs_color"] == (141.732, 19.685)

    # Turn the light on with XY color
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "xy_color": (0.5, 0.5),
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToColor(
                    colorX=0.5 * 65536,
                    colorY=0.5 * 65536,
                    transitionTime=0,
                    optionsMask=1,
                    optionsOverride=1,
                ),
            ),
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.OnOff.Commands.On(),
            ),
        ]
    )
    matter_client.send_device_command.reset_mock()

    # Turn the light on with XY color and custom transition
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "xy_color": (0.5, 0.5), "transition": 4.0},
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToColor(
                    colorX=0.5 * 65536,
                    colorY=0.5 * 65536,
                    transitionTime=40,
                    optionsMask=1,
                    optionsOverride=1,
                ),
            ),
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.OnOff.Commands.On(),
            ),
        ]
    )
    matter_client.send_device_command.reset_mock()

    # Turn the light on with HS color
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "hs_color": (236.69291338582678, 100.0),
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToHueAndSaturation(
                    hue=167,
                    saturation=254,
                    transitionTime=0,
                    optionsMask=1,
                    optionsOverride=1,
                ),
            ),
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.OnOff.Commands.On(),
            ),
        ]
    )
    matter_client.send_device_command.reset_mock()

    # Turn the light on with HS color and custom transition
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "hs_color": (236.69291338582678, 100.0),
            "transition": 4.0,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToHueAndSaturation(
                    hue=167,
                    saturation=254,
                    transitionTime=40,
                    optionsMask=1,
                    optionsOverride=1,
                ),
            ),
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.OnOff.Commands.On(),
            ),
        ]
    )
    matter_client.send_device_command.reset_mock()