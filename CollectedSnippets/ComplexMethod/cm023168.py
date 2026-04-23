async def test_property_sensor_door_status(
    hass: HomeAssistant, lock_august_pro, integration
) -> None:
    """Test property binary sensor with sensor mapping (doorStatus)."""
    node = lock_august_pro

    state = hass.states.get(PROPERTY_DOOR_STATUS_BINARY_SENSOR)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.DOOR

    # open door
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 6,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "doorStatus",
                "newValue": "open",
                "prevValue": "closed",
                "propertyName": "doorStatus",
            },
        },
    )
    node.receive_event(event)
    state = hass.states.get(PROPERTY_DOOR_STATUS_BINARY_SENSOR)
    assert state
    assert state.state == STATE_ON

    # close door
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 6,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "doorStatus",
                "newValue": "closed",
                "prevValue": "open",
                "propertyName": "doorStatus",
            },
        },
    )
    node.receive_event(event)
    state = hass.states.get(PROPERTY_DOOR_STATUS_BINARY_SENSOR)
    assert state
    assert state.state == STATE_OFF

    # door state unknown
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 6,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "doorStatus",
                "newValue": None,
                "prevValue": "open",
                "propertyName": "doorStatus",
            },
        },
    )
    node.receive_event(event)
    state = hass.states.get(PROPERTY_DOOR_STATUS_BINARY_SENSOR)
    assert state
    assert state.state == STATE_UNKNOWN