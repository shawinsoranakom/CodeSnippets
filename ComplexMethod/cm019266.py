async def test_sensors2(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    sensor_type: str,
    result: str,
    attributes: dict[str, Any],
) -> None:
    """Test the sensors."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": DEFAULT_NAME,
            "type": sensor_type,
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id",
        }
    }

    entity_ids = config["sensor"]["entities"]

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

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get(f"sensor.sensor_group_{sensor_type}")

    assert float(state.state) == pytest.approx(float(result))
    assert state.attributes.get(ATTR_ENTITY_ID) == entity_ids
    for key, value in attributes.items():
        assert state.attributes.get(key) == value
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.VOLUME
    assert state.attributes.get(ATTR_ICON) is None
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "L"

    entity = entity_registry.async_get(f"sensor.sensor_group_{sensor_type}")
    assert entity.unique_id == "very_unique_id"