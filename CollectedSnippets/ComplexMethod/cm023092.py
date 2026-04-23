async def test_value_removed_and_readded(
    hass: HomeAssistant,
    zp3111: Node,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test entity recovers when primary value is removed and re-added."""
    battery_level_entity = "sensor.4_in_1_sensor_battery_level"

    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state == "0.0"

    # Remove the battery level value
    event = Event(
        type="value removed",
        data={
            "source": "node",
            "event": "value removed",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Battery",
                "commandClass": 128,
                "endpoint": 0,
                "property": "level",
                "prevValue": 100,
                "propertyName": "level",
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Re-add the battery level value with a new reading
    event = Event(
        type="value added",
        data={
            "source": "node",
            "event": "value added",
            "nodeId": zp3111.node_id,
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
                "value": 80,
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "80.0"