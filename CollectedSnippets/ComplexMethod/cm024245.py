async def test_run_number_setup(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_class: str | None,
    unit_of_measurement: UnitOfTemperature | None,
    values: list[tuple[str, str]],
) -> None:
    """Test that it fetches the given payload."""
    await mqtt_mock_entry()

    for payload, value in values:
        async_fire_mqtt_message(hass, "test/state_number", payload)

        await hass.async_block_till_done()

        state = hass.states.get("number.test_number")
        assert state.state == value
        assert state.attributes.get(ATTR_DEVICE_CLASS) == device_class
        assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == unit_of_measurement

    async_fire_mqtt_message(hass, "test/state_number", "reset!")

    await hass.async_block_till_done()

    state = hass.states.get("number.test_number")
    assert state.state == "unknown"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == device_class
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == unit_of_measurement