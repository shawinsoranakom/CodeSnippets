async def test_unit_change(hass: HomeAssistant, zp3111, client, integration) -> None:
    """Test unit change via metadata updated event is handled by numeric sensors."""
    entity_id = "sensor.4_in_1_sensor_air_temperature"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "21.98"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    event = Event(
        "metadata updated",
        {
            "source": "node",
            "event": "metadata updated",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Multilevel Sensor",
                "commandClass": 49,
                "endpoint": 0,
                "property": "Air temperature",
                "metadata": {
                    "type": "number",
                    "readable": True,
                    "writeable": False,
                    "label": "Air temperature",
                    "ccSpecific": {"sensorType": 1, "scale": 1},
                    "unit": "°F",
                },
                "propertyName": "Air temperature",
                "nodeId": zp3111.node_id,
            },
        },
    )
    zp3111.receive_event(event)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "21.98"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    event = Event(
        "value updated",
        {
            "source": "node",
            "event": "value updated",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Multilevel Sensor",
                "commandClass": 49,
                "endpoint": 0,
                "property": "Air temperature",
                "newValue": 212,
                "prevValue": 21.98,
                "propertyName": "Air temperature",
            },
        },
    )
    zp3111.receive_event(event)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "100.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE