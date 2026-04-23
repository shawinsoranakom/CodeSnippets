async def test_shelly_wave_shutter_cover_with_tilt(
    hass: HomeAssistant,
    client: MagicMock,
    qubino_shutter_firmware_14_2_0: Node,
    integration: MockConfigEntry,
) -> None:
    """Test tilt function of the Shelly Wave Shutter with firmware 14.2.0.

    When parameter 71 is set to 1 (Venetian mode), endpoint 2 controls the tilt.
    """
    state = hass.states.get(SHELLY_WAVE_SHUTTER_COVER_ENTITY)
    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.SHUTTER

    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    # Test opening tilts
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: SHELLY_WAVE_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "endpoint": 2,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 99

    client.async_send_command.reset_mock()

    # Test closing tilts
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: SHELLY_WAVE_SHUTTER_COVER_ENTITY},
        blocking=True,
    )

    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "endpoint": 2,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test setting tilt position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: SHELLY_WAVE_SHUTTER_COVER_ENTITY, ATTR_TILT_POSITION: 12},
        blocking=True,
    )

    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "endpoint": 2,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 12

    # Test some tilt
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 5,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 2,
                "property": "currentValue",
                "newValue": 99,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    qubino_shutter_firmware_14_2_0.receive_event(event)
    state = hass.states.get(SHELLY_WAVE_SHUTTER_COVER_ENTITY)
    assert state
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100