async def test_generic_fan(
    hass: HomeAssistant, client, fan_generic, integration
) -> None:
    """Test the fan entity for a generic fan that lacks specific speed configuration."""
    node = fan_generic
    entity_id = "fan.generic_fan_controller"
    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_OFF

    # Test turn on no speed
    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 17
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 255

    client.async_send_command.reset_mock()

    # Due to optimistic updates, the state should be on even though the Z-Wave state
    # hasn't been updated yet
    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_ON

    # Test turn on setting speed
    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": entity_id, "percentage": 66},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 17
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 66

    client.async_send_command.reset_mock()

    # Test setting unknown speed
    with pytest.raises(MultipleInvalid):
        await hass.services.async_call(
            "fan",
            "set_percentage",
            {"entity_id": entity_id, "percentage": "bad"},
            blocking=True,
        )

    client.async_send_command.reset_mock()

    # Test turning off
    await hass.services.async_call(
        "fan",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 17
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test speed update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 17,
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

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 100

    client.async_send_command.reset_mock()

    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 17,
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

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_PERCENTAGE] == 0

    client.async_send_command.reset_mock()

    # Test setting percentage to 0
    await hass.services.async_call(
        "fan",
        SERVICE_SET_PERCENTAGE,
        {"entity_id": entity_id, "percentage": 0},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 17
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 0

    # Test value is None
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 17,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": None,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state.state == STATE_UNKNOWN