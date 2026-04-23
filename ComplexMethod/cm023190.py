async def test_numeric_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    multisensor_6,
    express_controls_ezmultipli,
    integration,
) -> None:
    """Test the numeric sensor."""
    state = hass.states.get(AIR_TEMPERATURE_SENSOR)

    assert state
    assert state.state == "9.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get(BATTERY_SENSOR)

    assert state
    assert state.state == "100.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.BATTERY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    entity_entry = entity_registry.async_get(BATTERY_SENSOR)
    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC

    state = hass.states.get(HUMIDITY_SENSOR)

    assert state
    assert state.state == "65.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.HUMIDITY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.multisensor_6_ultraviolet")

    assert state
    assert state.state == "0.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UV_INDEX
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.hsm200_illuminance")

    assert state
    assert state.state == "61.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    event = Event(
        "value updated",
        {
            "source": "node",
            "event": "value updated",
            "nodeId": express_controls_ezmultipli.node_id,
            "args": {
                "commandClassName": "Multilevel Sensor",
                "commandClass": 49,
                "endpoint": 0,
                "property": "Illuminance",
                "propertyName": "Illuminance",
                "newValue": None,
                "prevValue": 61,
            },
        },
    )

    express_controls_ezmultipli.receive_event(event)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.hsm200_illuminance")
    assert state
    assert state.state == STATE_UNKNOWN