async def test_spa_with_blower(hass: HomeAssistant, client: MagicMock) -> None:
    """Test supported features flags."""
    blower = MagicMock(SpaControl)
    blower.state = OffLowMediumHighState.OFF
    blower.options = list(OffLowMediumHighState)
    client.blowers = [blower]

    await init_integration(hass)

    state = hass.states.get(ENTITY_CLIMATE)

    assert state
    assert (
        state.attributes["supported_features"]
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_MIN_TEMP] == 10.0
    assert state.attributes[ATTR_MAX_TEMP] == 40.0
    assert state.attributes[ATTR_PRESET_MODE] == "ready"
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert state.attributes[ATTR_FAN_MODES] == ["off", "low", "medium", "high"]
    assert state.attributes[ATTR_FAN_MODE] == FAN_OFF

    for fan_mode in (FAN_LOW, FAN_MEDIUM, FAN_HIGH):
        client.blowers[0].set_state.reset_mock()
        state = await _patch_blower(hass, client, fan_mode)
        assert state.attributes[ATTR_FAN_MODE] == fan_mode
        client.blowers[0].set_state.assert_called_once()