async def test_equivalent_unit_of_measurement(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test device_class with equivalent unit of measurement."""
    assert await mqtt_mock_entry()
    async_fire_mqtt_message(hass, "test-topic", "100")
    await hass.async_block_till_done()
    state = hass.states.get("number.test")
    assert state is not None
    assert state.state == "100"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        is UnitOfElectricPotential.MICROVOLT
    )

    caplog.clear()

    discovery_payload = {
        "name": "bla",
        "command_topic": "test-topic2-cmd",
        "state_topic": "test-topic2",
        "unit_of_measurement": "\u00b5V",
    }
    # Now discover an invalid sensor
    async_fire_mqtt_message(
        hass, "homeassistant/number/bla/config", json.dumps(discovery_payload)
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "test-topic2", "21")
    await hass.async_block_till_done()
    state = hass.states.get("number.bla")
    assert state is not None
    assert state.state == "21"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        is UnitOfElectricPotential.MICROVOLT
    )