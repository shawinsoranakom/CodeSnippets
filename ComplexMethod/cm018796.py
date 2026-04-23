async def test_sensor_loaded_from_config_entry(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Test the sensor loaded from a config entry."""

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert state.attributes.get("buffer_usage_ratio") == round(9 / 20, 2)
    assert state.attributes.get("source_value_valid") is True
    assert "age_coverage_ratio" not in state.attributes