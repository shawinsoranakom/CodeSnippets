async def test_sensors_attributes_defined(hass: HomeAssistant) -> None:
    """Test the sensors."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": DEFAULT_NAME,
            "type": "sum",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id",
            "device_class": SensorDeviceClass.WATER,
            "state_class": SensorStateClass.TOTAL_INCREASING,
            "unit_of_measurement": "m³",
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_ids = config["sensor"]["entities"]

    for entity_id, value in dict(zip(entity_ids, VALUES, strict=False)).items():
        hass.states.async_set(
            entity_id,
            str(value),
            {
                ATTR_DEVICE_CLASS: SensorDeviceClass.VOLUME,
                ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
                ATTR_UNIT_OF_MEASUREMENT: "L",
            },
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.sensor_group_sum")

    # Liter to M3 = 1:0.001
    assert state.state == str(float(SUM_VALUE * 0.001))
    assert state.attributes.get(ATTR_ENTITY_ID) == entity_ids
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.WATER
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "m³"