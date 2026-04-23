async def test_color_temperature_light(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
    entity_id: str,
) -> None:
    """Test a color temperature light."""
    # Test that the light color temperature is 3000 (out of 50000)
    set_node_attribute(matter_node, 1, 768, 8, 2)
    set_node_attribute(matter_node, 1, 768, 7, 3000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert state.attributes["color_temp_kelvin"] == 333

    # Change color temperature
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "color_temp_kelvin": 3333,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToColorTemperature(
                    colorTemperatureMireds=300,
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
    # Change color temperature with 15 Kelvin to test capping of mireds at 65279
    # 15 Kelvin is 66666 Mireds which is above the maximum of 65279 Mireds permitted by Matter,
    # so it should be capped at 65279 mireds which is 15.3 Kelvin
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "color_temp_kelvin": 15,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToColorTemperature(
                    colorTemperatureMireds=65279,
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

    # Change color temperature with custom transition
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "color_temp_kelvin": 3333, "transition": 4.0},
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    matter_client.send_device_command.assert_has_calls(
        [
            call(
                node_id=matter_node.node_id,
                endpoint_id=1,
                command=clusters.ColorControl.Commands.MoveToColorTemperature(
                    colorTemperatureMireds=300,
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