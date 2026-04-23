async def test_sensors(hass: HomeAssistant, anova_api: AnovaApi) -> None:
    """Test setting up creates the sensors."""
    await async_init_integration(hass)
    assert len(hass.states.async_all("sensor")) == 8
    assert (
        hass.states.get("sensor.anova_precision_cooker_cook_time_remaining").state
        == "0"
    )
    assert hass.states.get("sensor.anova_precision_cooker_cook_time").state == "0"
    assert (
        hass.states.get("sensor.anova_precision_cooker_heater_temperature").state
        == "22.37"
    )
    assert hass.states.get("sensor.anova_precision_cooker_mode").state == "idle"
    assert hass.states.get("sensor.anova_precision_cooker_state").state == "no_state"
    assert (
        hass.states.get("sensor.anova_precision_cooker_target_temperature").state
        == "54.72"
    )
    assert (
        hass.states.get("sensor.anova_precision_cooker_water_temperature").state
        == "18.33"
    )
    assert (
        hass.states.get("sensor.anova_precision_cooker_triac_temperature").state
        == "36.04"
    )