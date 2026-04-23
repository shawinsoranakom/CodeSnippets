async def test_value_updated(
    hass: HomeAssistant, vision_security_zl7432, integration, client
) -> None:
    """Test value updated events."""
    node = vision_security_zl7432
    # Add states to the value we are updating to ensure the translation happens
    node.values["7-37-1-currentValue"].metadata.data["states"] = {"1": "on", "0": "off"}
    events = async_capture_events(hass, "zwave_js_value_updated")

    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 7,
            "args": {
                "commandClassName": "Switch Binary",
                "commandClass": 37,
                "endpoint": 1,
                "property": "currentValue",
                "newValue": 1,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )

    node.receive_event(event)
    # wait for the event
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["home_id"] == client.driver.controller.home_id
    assert events[0].data["node_id"] == 7
    assert events[0].data["entity_id"] == "switch.in_wall_dual_relay_switch"
    assert events[0].data["command_class"] == CommandClass.SWITCH_BINARY
    assert events[0].data["command_class_name"] == "Switch Binary"
    assert events[0].data["endpoint"] == 1
    assert events[0].data["property_name"] == "currentValue"
    assert events[0].data["property"] == "currentValue"
    assert events[0].data["value"] == "on"
    assert events[0].data["value_raw"] == 1

    # Try a value updated event on a value we aren't watching to make sure
    # no event fires
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 7,
            "args": {
                "commandClassName": "Basic",
                "commandClass": 32,
                "endpoint": 1,
                "property": "currentValue",
                "newValue": 1,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )

    node.receive_event(event)
    # wait for the event
    await hass.async_block_till_done()
    # We should only still have captured one event
    assert len(events) == 1