async def test_aeotec_nano_shutter_cover(
    hass: HomeAssistant,
    client: MagicMock,
    aeotec_nano_shutter: Node,
    integration: MockConfigEntry,
) -> None:
    """Test movement of an Aeotec Nano Shutter cover entity. Useful to make sure the stop command logic is handled properly."""
    node = aeotec_nano_shutter
    state = hass.states.get(AEOTEC_SHUTTER_COVER_ENTITY)

    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.WINDOW

    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    # Test opening
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: AEOTEC_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 3
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
        {ATTR_ENTITY_ID: AEOTEC_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    open_args = client.async_send_command.call_args_list[0][0][0]
    assert open_args["command"] == "node.set_value"
    assert open_args["nodeId"] == 3
    assert open_args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "On",
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

    state = hass.states.get(AEOTEC_SHUTTER_COVER_ENTITY)
    assert state.state == CoverState.OPEN

    # Test closing
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: AEOTEC_SHUTTER_COVER_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 3
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
        {ATTR_ENTITY_ID: AEOTEC_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    open_args = client.async_send_command.call_args_list[0][0][0]
    assert open_args["command"] == "node.set_value"
    assert open_args["nodeId"] == 3
    assert open_args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "On",
    }
    assert not open_args["value"]