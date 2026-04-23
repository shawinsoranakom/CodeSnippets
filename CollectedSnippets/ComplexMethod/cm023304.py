async def test_nice_ibt4zwave_cover(
    hass: HomeAssistant,
    client: MagicMock,
    nice_ibt4zwave: Node,
    integration: MockConfigEntry,
) -> None:
    """Test Nice IBT4ZWAVE cover."""
    entity_id = "cover.portail"
    state = hass.states.get(entity_id)
    assert state
    # This device has no state because there is no position value
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == (
        CoverEntityFeature.CLOSE
        | CoverEntityFeature.OPEN
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
    )
    assert ATTR_CURRENT_POSITION in state.attributes
    assert state.attributes[ATTR_CURRENT_POSITION] == 0
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.GATE

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 72
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 72
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 99

    client.async_send_command.reset_mock()