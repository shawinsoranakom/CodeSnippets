async def test_motor_barrier_cover(
    hass: HomeAssistant,
    client: MagicMock,
    gdc_zw062: Node,
    integration: MockConfigEntry,
) -> None:
    """Test the cover entity."""
    node = gdc_zw062

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.GARAGE

    assert state.state == CoverState.CLOSED

    # Test open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: GDC_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 12
    assert args["value"] == 255
    assert args["valueId"] == {
        "commandClass": 102,
        "endpoint": 0,
        "property": "targetState",
    }

    # state doesn't change until currentState value update is received
    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.CLOSED

    client.async_send_command.reset_mock()

    # Test close
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: GDC_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 12
    assert args["value"] == 0
    assert args["valueId"] == {
        "commandClass": 102,
        "endpoint": 0,
        "property": "targetState",
    }

    # state doesn't change until currentState value update is received
    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.CLOSED

    client.async_send_command.reset_mock()

    # Barrier sends an opening state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 12,
            "args": {
                "commandClassName": "Barrier Operator",
                "commandClass": 102,
                "endpoint": 0,
                "property": "currentState",
                "newValue": 254,
                "prevValue": 0,
                "propertyName": "currentState",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.OPENING

    # Barrier sends an opened state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 12,
            "args": {
                "commandClassName": "Barrier Operator",
                "commandClass": 102,
                "endpoint": 0,
                "property": "currentState",
                "newValue": 255,
                "prevValue": 254,
                "propertyName": "currentState",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.OPEN

    # Barrier sends a closing state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 12,
            "args": {
                "commandClassName": "Barrier Operator",
                "commandClass": 102,
                "endpoint": 0,
                "property": "currentState",
                "newValue": 252,
                "prevValue": 255,
                "propertyName": "currentState",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.CLOSING

    # Barrier sends a closed state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 12,
            "args": {
                "commandClassName": "Barrier Operator",
                "commandClass": 102,
                "endpoint": 0,
                "property": "currentState",
                "newValue": 0,
                "prevValue": 252,
                "propertyName": "currentState",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == CoverState.CLOSED

    # Barrier sends a stopped state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 12,
            "args": {
                "commandClassName": "Barrier Operator",
                "commandClass": 102,
                "endpoint": 0,
                "property": "currentState",
                "newValue": 253,
                "prevValue": 252,
                "propertyName": "currentState",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(GDC_COVER_ENTITY)
    assert state.state == STATE_UNKNOWN