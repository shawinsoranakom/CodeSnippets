async def test_barrier_signaling_switch(
    hass: HomeAssistant, gdc_zw062, integration, client
) -> None:
    """Test barrier signaling state switch."""
    node = gdc_zw062
    entity = "switch.aeon_labs_garage_door_controller_gen5_signaling_state_visual"

    state = hass.states.get(entity)
    assert state
    assert state.state == "on"

    # Test turning off
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {"entity_id": entity}, blocking=True
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 12
    assert args["value"] == 0
    assert args["valueId"] == {
        "commandClass": 102,
        "endpoint": 0,
        "property": "signalingState",
        "propertyKey": 2,
    }

    # state change is optimistic and writes state
    await hass.async_block_till_done()

    state = hass.states.get(entity)
    assert state.state == STATE_OFF

    client.async_send_command.reset_mock()

    # Test turning on
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {"entity_id": entity}, blocking=True
    )

    # Note: the valueId's value is still 255 because we never
    # received an updated value
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 12
    assert args["value"] == 255
    assert args["valueId"] == {
        "commandClass": 102,
        "endpoint": 0,
        "property": "signalingState",
        "propertyKey": 2,
    }

    # state change is optimistic and writes state
    await hass.async_block_till_done()

    state = hass.states.get(entity)
    assert state.state == STATE_ON

    # Received a refresh off
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
                "property": "signalingState",
                "propertyKey": 2,
                "newValue": 0,
                "prevValue": 0,
                "propertyName": "signalingState",
                "propertyKeyName": "2",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity)
    assert state.state == STATE_OFF

    # Received a refresh off
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
                "property": "signalingState",
                "propertyKey": 2,
                "newValue": 255,
                "prevValue": 255,
                "propertyName": "signalingState",
                "propertyKeyName": "2",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity)
    assert state.state == STATE_ON