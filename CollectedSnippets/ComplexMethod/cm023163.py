async def test_notifications(
    hass: HomeAssistant, hank_binary_switch, integration, client
) -> None:
    """Test notification events."""
    # just pick a random node to fake the value notification events
    node = hank_binary_switch
    events = async_capture_events(hass, "zwave_js_notification")

    # Publish fake Notification CC notification
    event = Event(
        type="notification",
        data={
            "source": "node",
            "event": "notification",
            "nodeId": 32,
            "endpointIndex": 0,
            "ccId": 113,
            "args": {
                "type": 6,
                "event": 5,
                "label": "Access Control",
                "eventLabel": "Keypad lock operation",
                "parameters": {"userId": 1},
            },
        },
    )
    node.receive_event(event)
    # wait for the event
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["home_id"] == client.driver.controller.home_id
    assert events[0].data["node_id"] == 32
    assert events[0].data["endpoint"] == 0
    assert events[0].data["type"] == 6
    assert events[0].data["event"] == 5
    assert events[0].data["label"] == "Access Control"
    assert events[0].data["event_label"] == "Keypad lock operation"
    assert events[0].data["parameters"]["userId"] == 1
    assert events[0].data["command_class"] == CommandClass.NOTIFICATION
    assert events[0].data["command_class_name"] == "Notification"

    # Publish fake Entry Control CC notification
    event = Event(
        type="notification",
        data={
            "source": "node",
            "event": "notification",
            "nodeId": 32,
            "endpointIndex": 0,
            "ccId": 111,
            "args": {
                "eventType": 5,
                "eventTypeLabel": "test1",
                "dataType": 2,
                "dataTypeLabel": "test2",
                "eventData": "555",
            },
        },
    )

    node.receive_event(event)
    # wait for the event
    await hass.async_block_till_done()
    assert len(events) == 2
    assert events[1].data["home_id"] == client.driver.controller.home_id
    assert events[1].data["node_id"] == 32
    assert events[0].data["endpoint"] == 0
    assert events[1].data["event_type"] == 5
    assert events[1].data["event_type_label"] == "test1"
    assert events[1].data["data_type"] == 2
    assert events[1].data["data_type_label"] == "test2"
    assert events[1].data["event_data"] == "555"
    assert events[1].data["command_class"] == CommandClass.ENTRY_CONTROL
    assert events[1].data["command_class_name"] == "Entry Control"

    # Publish fake Multilevel Switch CC notification
    event = Event(
        type="notification",
        data={
            "source": "node",
            "event": "notification",
            "nodeId": 32,
            "endpointIndex": 0,
            "ccId": 38,
            "args": {"eventType": 4, "eventTypeLabel": "test1", "direction": "up"},
        },
    )

    node.receive_event(event)
    # wait for the event
    await hass.async_block_till_done()
    assert len(events) == 3
    assert events[2].data["home_id"] == client.driver.controller.home_id
    assert events[2].data["node_id"] == 32
    assert events[0].data["endpoint"] == 0
    assert events[2].data["event_type"] == 4
    assert events[2].data["event_type_label"] == "test1"
    assert events[2].data["direction"] == "up"
    assert events[2].data["command_class"] == CommandClass.SWITCH_MULTILEVEL
    assert events[2].data["command_class_name"] == "Multilevel Switch"