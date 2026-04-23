async def test_volume_number(
    hass: HomeAssistant, client, aeotec_zw164_siren, integration
) -> None:
    """Test the volume number entity."""
    node = aeotec_zw164_siren
    state = hass.states.get(VOLUME_NUMBER_ENTITY)

    assert state
    assert state.state == "1.0"
    assert state.attributes["step"] == 0.01
    assert state.attributes["max"] == 1.0
    assert state.attributes["min"] == 0

    # Test turn on setting value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": VOLUME_NUMBER_ENTITY, "value": 0.3},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "endpoint": 2,
        "commandClass": 121,
        "property": "defaultVolume",
    }
    assert args["value"] == 30

    client.async_send_command.reset_mock()

    # Test value update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 4,
            "args": {
                "commandClassName": "Sound Switch",
                "commandClass": 121,
                "endpoint": 2,
                "property": "defaultVolume",
                "newValue": 30,
                "prevValue": 100,
                "propertyName": "defaultVolume",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(VOLUME_NUMBER_ENTITY)
    assert state.state == "0.3"

    # Test null value
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 4,
            "args": {
                "commandClassName": "Sound Switch",
                "commandClass": 121,
                "endpoint": 2,
                "property": "defaultVolume",
                "newValue": None,
                "prevValue": 30,
                "propertyName": "defaultVolume",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(VOLUME_NUMBER_ENTITY)
    assert state.state == STATE_UNKNOWN