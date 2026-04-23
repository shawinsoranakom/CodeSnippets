async def test_sensors_attributes_added_when_entity_info_available(
    hass: HomeAssistant,
) -> None:
    """Test the sensor calculate attributes once all entities attributes are available."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": DEFAULT_NAME,
            "type": "sum",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id",
        }
    }

    entity_ids = config["sensor"]["entities"]

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.sensor_group_sum")

    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get(ATTR_ENTITY_ID) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    for entity_id, value in dict(zip(entity_ids, VALUES, strict=False)).items():
        hass.states.async_set(
            entity_id,
            str(value),
            {
                ATTR_DEVICE_CLASS: SensorDeviceClass.VOLUME,
                ATTR_STATE_CLASS: SensorStateClass.TOTAL,
                ATTR_UNIT_OF_MEASUREMENT: "L",
            },
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.sensor_group_sum")

    assert float(state.state) == pytest.approx(float(SUM_VALUE))
    assert state.attributes.get(ATTR_ENTITY_ID) == entity_ids
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.VOLUME
    assert state.attributes.get(ATTR_ICON) is None
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "L"