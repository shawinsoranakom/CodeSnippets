async def test_iblinds_v3_cover(
    hass: HomeAssistant,
    client: MagicMock,
    iblinds_v3: Node,
    integration: MockConfigEntry,
) -> None:
    """Test iBlinds v3 cover which uses Window Covering CC."""
    entity_id = "cover.blind_west_bed_1_horizontal_slats_angle"
    state = hass.states.get(entity_id)
    assert state
    # This device has no state because there is no position value
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == (
        CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.SET_TILT_POSITION
        | CoverEntityFeature.STOP_TILT
    )
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION in state.attributes
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 131
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 106,
        "property": "targetValue",
        "propertyKey": 23,
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 131
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 106,
        "property": "targetValue",
        "propertyKey": 23,
    }
    assert args["value"] == 50

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_TILT_POSITION: 12},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 131
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 106,
        "property": "targetValue",
        "propertyKey": 23,
    }
    assert args["value"] == 12

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 131
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 106,
        "property": "levelChangeUp",
        "propertyKey": 23,
    }
    assert args["value"] is False

    client.async_send_command.reset_mock()