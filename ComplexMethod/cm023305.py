async def test_window_covering_open_close(
    hass: HomeAssistant,
    client: MagicMock,
    window_covering_outbound_bottom: Node,
    integration: MockConfigEntry,
) -> None:
    """Test Window Covering device open and close commands.

    A Window Covering device with position support
    should be able to open/close with the start/stop level change properties.
    """
    entity_id = "cover.node_2_outbound_bottom"
    state = hass.states.get(entity_id)

    # The entity has position support, but not tilt
    assert state
    assert ATTR_CURRENT_POSITION in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Test opening
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 106,
        "endpoint": 0,
        "property": "levelChangeUp",
        "propertyKey": 13,
    }
    assert args["value"] is True

    client.async_send_command.reset_mock()

    # Test stop after opening
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 106,
        "endpoint": 0,
        "property": "levelChangeUp",
        "propertyKey": 13,
    }
    assert args["value"] is False

    client.async_send_command.reset_mock()

    # Test closing
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 106,
        "endpoint": 0,
        "property": "levelChangeDown",
        "propertyKey": 13,
    }
    assert args["value"] is True

    client.async_send_command.reset_mock()

    # Test stop after closing
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 106,
        "endpoint": 0,
        "property": "levelChangeUp",
        "propertyKey": 13,
    }
    assert args["value"] is False

    client.async_send_command.reset_mock()