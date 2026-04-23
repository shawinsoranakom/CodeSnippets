async def test_temperature_validation(
    hass: HomeAssistant, register_test_integration: MockConfigEntry
) -> None:
    """Test validation for temperatures."""

    class MockClimateEntityTemp(MockClimateEntity):
        """Mock climate class with mocked aux heater."""

        _attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        _attr_target_temperature = 15
        _attr_target_temperature_high = 18
        _attr_target_temperature_low = 10
        _attr_target_temperature_step = PRECISION_WHOLE

        def set_temperature(self, **kwargs: Any) -> None:
            """Set new target temperature."""
            if ATTR_TEMPERATURE in kwargs:
                self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
            if ATTR_TARGET_TEMP_HIGH in kwargs:
                self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
                self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]

    test_climate = MockClimateEntityTemp(
        name="Test",
        unique_id="unique_climate_test",
    )

    setup_test_component_platform(
        hass, DOMAIN, entities=[test_climate], from_config_entry=True
    )
    await hass.config_entries.async_setup(register_test_integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("climate.test")
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) is None
    assert state.attributes.get(ATTR_MIN_TEMP) == 7
    assert state.attributes.get(ATTR_MAX_TEMP) == 35

    with pytest.raises(
        ServiceValidationError,
        match="Provided temperature 40.0 is not valid. Accepted range is 7 to 35",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test",
                ATTR_TEMPERATURE: "40",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Provided temperature 40.0 is not valid. Accepted range is 7 to 35"
    )
    assert exc.value.translation_key == "temp_out_of_range"

    with pytest.raises(
        ServiceValidationError,
        match="Provided temperature 0.0 is not valid. Accepted range is 7 to 35",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test",
                ATTR_TARGET_TEMP_HIGH: "25",
                ATTR_TARGET_TEMP_LOW: "0",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Provided temperature 0.0 is not valid. Accepted range is 7 to 35"
    )
    assert exc.value.translation_key == "temp_out_of_range"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": "climate.test",
            ATTR_TARGET_TEMP_HIGH: "25",
            ATTR_TARGET_TEMP_LOW: "10",
        },
        blocking=True,
    )

    state = hass.states.get("climate.test")
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 10
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 25