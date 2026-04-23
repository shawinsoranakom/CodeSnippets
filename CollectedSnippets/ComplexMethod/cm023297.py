async def test_window_cover(
    hass: HomeAssistant,
    client: MagicMock,
    chain_actuator_zws12: Node,
    integration: MockConfigEntry,
) -> None:
    """Test the cover entity."""
    node = chain_actuator_zws12
    state = hass.states.get(WINDOW_COVER_ENTITY)

    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.WINDOW

    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    # Test setting position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY, ATTR_POSITION: 50},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 6
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 50

    client.async_send_command.reset_mock()

    # Test setting position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY, ATTR_POSITION: 0},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 6
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test opening
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 6
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"]

    client.async_send_command.reset_mock()

    # Test stop after opening
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    open_args = client.async_send_command.call_args_list[0][0][0]
    assert open_args["command"] == "node.set_value"
    assert open_args["nodeId"] == 6
    assert open_args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "Open",
    }
    assert not open_args["value"]

    # Test position update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 6,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 99,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)
    client.async_send_command.reset_mock()

    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.OPEN

    # Test closing
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 6
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test stop after closing
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    open_args = client.async_send_command.call_args_list[0][0][0]
    assert open_args["command"] == "node.set_value"
    assert open_args["nodeId"] == 6
    assert open_args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "Open",
    }
    assert not open_args["value"]

    client.async_send_command.reset_mock()

    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 6,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 0,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.CLOSED