async def test_spa_defaults_fake_tscale(
    hass: HomeAssistant, client: MagicMock, integration: MockConfigEntry
) -> None:
    """Test supported features flags."""
    client.temperature_unit = 1

    state = hass.states.get(ENTITY_CLIMATE)

    assert state
    assert (
        state.attributes["supported_features"]
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_MIN_TEMP] == 10.0
    assert state.attributes[ATTR_MAX_TEMP] == 40.0
    assert state.attributes[ATTR_PRESET_MODE] == "ready"
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE