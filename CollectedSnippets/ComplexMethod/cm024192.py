async def test_device_class_with_equivalent_unit_of_measurement_received(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
    device_class: str,
    unit: StrEnum,
    equivalent_unit: str,
) -> None:
    """Test device_class with equivalent unit of measurement."""
    assert await mqtt_mock_entry()
    async_fire_mqtt_message(hass, "test-topic", "100")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == "100"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is unit

    caplog.clear()

    discovery_payload = {
        "name": "bla",
        "state_topic": "test-topic2",
        "device_class": device_class,
        "unit_of_measurement": equivalent_unit,
    }
    # Now discover a sensor with an ambiguous unit
    async_fire_mqtt_message(
        hass, "homeassistant/sensor/bla/config", json.dumps(discovery_payload)
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "test-topic2", "21")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.bla")
    assert state is not None
    assert state.state == "21"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is unit