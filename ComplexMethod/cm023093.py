async def test_value_never_populated_then_added(
    hass: HomeAssistant,
    zp3111_state: NodeDataType,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test entity updates when value metadata exists but value is None, then added."""
    # Modify the battery level value to have value=None (metadata exists but no data)
    node_state = deepcopy(zp3111_state)
    for value in node_state["values"]:
        if value["commandClass"] == 128 and value["property"] == "level":
            value["value"] = None
            break

    event = Event(
        "node added",
        {
            "source": "controller",
            "event": "node added",
            "node": node_state,
            "result": {},
        },
    )
    client.driver.controller.receive_event(event)
    await hass.async_block_till_done()

    # The entity should exist but have unknown state (value is None)
    battery_level_entity = "sensor.4_in_1_sensor_battery_level"
    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state == STATE_UNKNOWN

    node = client.driver.controller.nodes[node_state["nodeId"]]

    # Now send "value added" event with actual value
    event = Event(
        type="value added",
        data={
            "source": "node",
            "event": "value added",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Battery",
                "commandClass": 128,
                "endpoint": 0,
                "property": "level",
                "propertyName": "level",
                "metadata": {
                    "type": "number",
                    "readable": True,
                    "writeable": False,
                    "label": "Battery level",
                    "min": 0,
                    "max": 100,
                    "unit": "%",
                },
                "value": 75,
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state == "75.0"