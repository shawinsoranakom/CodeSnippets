async def test_switch(
    hass: HomeAssistant, hank_binary_switch, integration, client
) -> None:
    """Test the switch."""
    state = hass.states.get(SWITCH_ENTITY)
    node = hank_binary_switch

    assert state
    assert state.state == STATE_OFF

    # Test turning on
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": SWITCH_ENTITY}, blocking=True
    )

    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 32
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] is True

    # Test state updates from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 32,
            "args": {
                "commandClassName": "Binary Switch",
                "commandClass": 37,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": True,
                "prevValue": False,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(SWITCH_ENTITY)
    assert state.state == "on"

    client.async_send_command.reset_mock()

    # Test turning off
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH_ENTITY}, blocking=True
    )

    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 32
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] is False