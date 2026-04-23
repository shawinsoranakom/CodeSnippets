async def test_native_value_validation(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test state validation and native value conversion."""
    mqtt_mock = await mqtt_mock_entry()

    async_fire_mqtt_message(hass, "test/state_number", "23.5")
    state = hass.states.get("number.test_number")
    assert state is not None
    assert state.attributes.get(ATTR_MIN) == 15
    assert state.attributes.get(ATTR_MAX) == 28
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfTemperature.CELSIUS.value
    )
    assert state.state == "23.5"

    # Test out of range validation
    async_fire_mqtt_message(hass, "test/state_number", "29.5")
    state = hass.states.get("number.test_number")
    assert state is not None
    assert state.attributes.get(ATTR_MIN) == 15
    assert state.attributes.get(ATTR_MAX) == 28
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfTemperature.CELSIUS.value
    )
    assert state.state == "23.5"
    assert (
        "Invalid value for number.test_number: 29.5 (range 15.0 - 28.0)" in caplog.text
    )
    caplog.clear()

    # Check if validation still works when changing unit system
    hass.config.units = US_CUSTOMARY_SYSTEM
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "test/state_number", "24.5")
    state = hass.states.get("number.test_number")
    assert state is not None
    assert state.attributes.get(ATTR_MIN) == 59.0
    assert state.attributes.get(ATTR_MAX) == 82.4
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfTemperature.FAHRENHEIT.value
    )
    assert state.state == "76.1"

    # Test out of range validation again
    async_fire_mqtt_message(hass, "test/state_number", "29.5")
    state = hass.states.get("number.test_number")
    assert state is not None
    assert state.attributes.get(ATTR_MIN) == 59.0
    assert state.attributes.get(ATTR_MAX) == 82.4
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfTemperature.FAHRENHEIT.value
    )
    assert state.state == "76.1"
    assert (
        "Invalid value for number.test_number: 29.5 (range 15.0 - 28.0)" in caplog.text
    )
    caplog.clear()

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.test_number", ATTR_VALUE: 68},
        blocking=True,
    )

    mqtt_mock.async_publish.assert_called_once_with("test/cmd_number", "20", 0, False)
    mqtt_mock.async_publish.reset_mock()