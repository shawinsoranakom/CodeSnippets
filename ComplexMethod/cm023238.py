async def test_number(
    hass: HomeAssistant, client, aeotec_radiator_thermostat, integration
) -> None:
    """Test the number entity."""
    node = aeotec_radiator_thermostat
    state = hass.states.get(NUMBER_ENTITY)

    assert state
    assert state.state == "75.0"

    # Test turn on setting value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NUMBER_ENTITY, "value": 30},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 4
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
    }
    assert args["value"] == 30.0

    client.async_send_command.reset_mock()

    # Test value update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 4,
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

    state = hass.states.get(NUMBER_ENTITY)
    assert state.state == "99.0"