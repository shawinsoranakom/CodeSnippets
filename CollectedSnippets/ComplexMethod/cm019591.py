async def test_vacuum_actions(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test vacuum entity actions."""
    # Fetch translations
    await async_setup_component(hass, "homeassistant", {})
    entity_id = "vacuum.mock_vacuum"
    state = hass.states.get(entity_id)
    assert state

    # test return_to_base action
    await hass.services.async_call(
        "vacuum",
        "return_to_base",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.RvcOperationalState.Commands.GoHome(),
    )
    matter_client.send_device_command.reset_mock()

    # test start action (from idle state)
    await hass.services.async_call(
        "vacuum",
        "start",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 2
    assert matter_client.send_device_command.call_args_list[0] == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.ServiceArea.Commands.SelectAreas(newAreas=[]),
    )
    assert matter_client.send_device_command.call_args_list[1] == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.RvcRunMode.Commands.ChangeToMode(newMode=1),
    )
    matter_client.send_device_command.reset_mock()

    # test resume action (from paused state)
    # first set the operational state to paused
    set_node_attribute(matter_node, 1, 97, 4, 0x02)
    await trigger_subscription_callback(hass, matter_client)

    await hass.services.async_call(
        "vacuum",
        "start",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.RvcOperationalState.Commands.Resume(),
    )
    matter_client.send_device_command.reset_mock()

    # test pause action
    await hass.services.async_call(
        "vacuum",
        "pause",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.RvcOperationalState.Commands.Pause(),
    )
    matter_client.send_device_command.reset_mock()

    # test stop action
    await hass.services.async_call(
        "vacuum",
        "stop",
        {
            "entity_id": entity_id,
        },
        blocking=True,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.RvcRunMode.Commands.ChangeToMode(newMode=0),
    )
    matter_client.send_device_command.reset_mock()