async def test_mode_validation(
    hass: HomeAssistant,
    register_test_integration: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test mode validation for hvac_mode, fan, swing and preset."""
    climate_entity = MockClimateEntity(name="test", entity_id="climate.test")

    setup_test_component_platform(
        hass, DOMAIN, entities=[climate_entity], from_config_entry=True
    )
    await hass.config_entries.async_setup(register_test_integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("climate.test")
    assert state.state == "heat"
    assert state.attributes.get(ATTR_PRESET_MODE) == "home"
    assert state.attributes.get(ATTR_FAN_MODE) == "auto"
    assert state.attributes.get(ATTR_SWING_MODE) == "auto"
    assert state.attributes.get(ATTR_SWING_HORIZONTAL_MODE) == "on"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": "climate.test",
            "preset_mode": "away",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_MODE,
        {
            "entity_id": "climate.test",
            "swing_mode": "off",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_HORIZONTAL_MODE,
        {
            "entity_id": "climate.test",
            "swing_horizontal_mode": "off",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_MODE,
        {
            "entity_id": "climate.test",
            "fan_mode": "off",
        },
        blocking=True,
    )
    state = hass.states.get("climate.test")
    assert state.attributes.get(ATTR_PRESET_MODE) == "away"
    assert state.attributes.get(ATTR_FAN_MODE) == "off"
    assert state.attributes.get(ATTR_SWING_MODE) == "off"
    assert state.attributes.get(ATTR_SWING_HORIZONTAL_MODE) == "off"

    with pytest.raises(
        ServiceValidationError,
        match="HVAC mode auto is not valid. Valid HVAC modes are: off, heat",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                "entity_id": "climate.test",
                "hvac_mode": "auto",
            },
            blocking=True,
        )
    assert (
        str(exc.value) == "HVAC mode auto is not valid. Valid HVAC modes are: off, heat"
    )
    assert exc.value.translation_key == "not_valid_hvac_mode"

    with pytest.raises(
        ServiceValidationError,
        match="Preset mode invalid is not valid. Valid preset modes are: home, away",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                "entity_id": "climate.test",
                "preset_mode": "invalid",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Preset mode invalid is not valid. Valid preset modes are: home, away"
    )
    assert exc.value.translation_key == "not_valid_preset_mode"

    with pytest.raises(
        ServiceValidationError,
        match="Swing mode invalid is not valid. Valid swing modes are: auto, off",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_MODE,
            {
                "entity_id": "climate.test",
                "swing_mode": "invalid",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Swing mode invalid is not valid. Valid swing modes are: auto, off"
    )
    assert exc.value.translation_key == "not_valid_swing_mode"

    with pytest.raises(
        ServiceValidationError,
        match="Horizontal swing mode invalid is not valid. Valid horizontal swing modes are: on, off",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_HORIZONTAL_MODE,
            {
                "entity_id": "climate.test",
                "swing_horizontal_mode": "invalid",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Horizontal swing mode invalid is not valid. Valid horizontal swing modes are: on, off"
    )
    assert exc.value.translation_key == "not_valid_horizontal_swing_mode"

    with pytest.raises(
        ServiceValidationError,
        match="Fan mode invalid is not valid. Valid fan modes are: auto, off",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_MODE,
            {
                "entity_id": "climate.test",
                "fan_mode": "invalid",
            },
            blocking=True,
        )
    assert (
        str(exc.value)
        == "Fan mode invalid is not valid. Valid fan modes are: auto, off"
    )
    assert exc.value.translation_key == "not_valid_fan_mode"