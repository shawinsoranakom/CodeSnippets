async def test_dimmable_light(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
    entity_id: str,
) -> None:
    """Test a dimmable light."""

    # Test for currentLevel is None
    set_node_attribute(matter_node, 1, 8, 0, None)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["brightness"] is None

    # Test that the light brightness is 50 (out of 254)
    set_node_attribute(matter_node, 1, 8, 0, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["brightness"] == 49

    # Change brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity_id,
            "brightness": 128,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.LevelControl.Commands.MoveToLevelWithOnOff(
            level=128,
            transitionTime=0,
        ),
    )
    matter_client.send_device_command.reset_mock()

    # Change brightness with custom transition
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity_id, "brightness": 128, "transition": 3},
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.LevelControl.Commands.MoveToLevelWithOnOff(
            level=128,
            transitionTime=30,
        ),
    )
    matter_client.send_device_command.reset_mock()