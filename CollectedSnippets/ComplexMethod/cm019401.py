async def test_adam_climate_off_mode_change(
    hass: HomeAssistant,
    mock_smile_adam_jip: MagicMock,
    init_integration: MockConfigEntry,
) -> None:
    """Test handling of user requests in adam climate device environment."""
    state = hass.states.get("climate.slaapkamer")
    assert state
    assert state.state == HVACMode.OFF
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: "climate.slaapkamer",
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )
    assert mock_smile_adam_jip.set_schedule_state.call_count == 0
    assert mock_smile_adam_jip.set_regulation_mode.call_count == 1
    mock_smile_adam_jip.set_regulation_mode.assert_called_with("heating")

    state = hass.states.get("climate.kinderkamer")
    assert state
    assert state.state == HVACMode.HEAT
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: "climate.kinderkamer",
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )
    assert mock_smile_adam_jip.set_schedule_state.call_count == 0
    assert mock_smile_adam_jip.set_regulation_mode.call_count == 2
    mock_smile_adam_jip.set_regulation_mode.assert_called_with("off")

    state = hass.states.get("climate.logeerkamer")
    assert state
    assert state.state == HVACMode.HEAT
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: "climate.logeerkamer",
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )
    assert mock_smile_adam_jip.set_schedule_state.call_count == 0
    assert mock_smile_adam_jip.set_regulation_mode.call_count == 2