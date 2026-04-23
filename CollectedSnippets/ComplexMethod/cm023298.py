async def test_fibaro_fgr222_shutter_cover(
    hass: HomeAssistant,
    client: MagicMock,
    fibaro_fgr222_shutter: Node,
    integration: MockConfigEntry,
) -> None:
    """Test tilt function of the Fibaro Shutter devices."""
    state = hass.states.get(FIBARO_FGR_222_SHUTTER_COVER_ENTITY)
    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.SHUTTER

    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    # Test opening tilts
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: FIBARO_FGR_222_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 42
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 145,
        "property": "fibaro",
        "propertyKey": "venetianBlindsTilt",
    }
    assert args["value"] == 99

    client.async_send_command.reset_mock()

    # Test closing tilts
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: FIBARO_FGR_222_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 42
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 145,
        "property": "fibaro",
        "propertyKey": "venetianBlindsTilt",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test setting tilt position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: FIBARO_FGR_222_SHUTTER_COVER_ENTITY, ATTR_TILT_POSITION: 12},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 42
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 145,
        "property": "fibaro",
        "propertyKey": "venetianBlindsTilt",
    }
    assert args["value"] == 12

    # Test some tilt
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 42,
            "args": {
                "commandClassName": "Manufacturer Proprietary",
                "commandClass": 145,
                "endpoint": 0,
                "property": "fibaro",
                "propertyKey": "venetianBlindsTilt",
                "newValue": 99,
                "prevValue": 0,
                "propertyName": "fibaro",
                "propertyKeyName": "venetianBlindsTilt",
            },
        },
    )
    fibaro_fgr222_shutter.receive_event(event)
    state = hass.states.get(FIBARO_FGR_222_SHUTTER_COVER_ENTITY)
    assert state
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100