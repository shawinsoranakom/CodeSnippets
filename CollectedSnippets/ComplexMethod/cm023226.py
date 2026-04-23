async def test_basic_cc_light(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    ge_in_wall_dimmer_switch,
    integration,
) -> None:
    """Test light is created from Basic CC."""
    node = ge_in_wall_dimmer_switch

    entity_entry = entity_registry.async_get(BASIC_LIGHT_ENTITY)

    assert entity_entry
    assert not entity_entry.disabled

    state = hass.states.get(BASIC_LIGHT_ENTITY)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes["supported_features"] == 0

    # Send value to 0
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 2,
            "args": {
                "commandClassName": "Basic",
                "commandClass": 32,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 0,
                "prevValue": None,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(BASIC_LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Turn on light
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BASIC_LIGHT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 32,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 255

    # Due to optimistic updates, the state should be on even though the Z-Wave state
    # hasn't been updated yet
    state = hass.states.get(BASIC_LIGHT_ENTITY)

    assert state
    assert state.state == STATE_ON

    client.async_send_command.reset_mock()

    # Send value to 0
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 2,
            "args": {
                "commandClassName": "Basic",
                "commandClass": 32,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 0,
                "prevValue": None,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(BASIC_LIGHT_ENTITY)
    assert state
    assert state.state == STATE_OFF

    # Turn on light with brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BASIC_LIGHT_ENTITY, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 32,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 50

    # Since we specified a brightness, there is no optimistic update so the state
    # should be off
    state = hass.states.get(BASIC_LIGHT_ENTITY)

    assert state
    assert state.state == STATE_OFF

    client.async_send_command.reset_mock()

    # Turn off light
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": BASIC_LIGHT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 32,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 0