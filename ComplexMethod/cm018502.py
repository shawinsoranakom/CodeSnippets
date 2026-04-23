async def test_rpc_pulse_counter_frequency_sensors(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
    original_unit: str | None,
    expected_unit: str | None,
) -> None:
    """Test RPC counter sensor."""
    config = deepcopy(mock_rpc_device.config)
    config["input:2"]["xfreq"] = {"expr": "x**2", "unit": original_unit}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    await init_integration(hass, 2)

    entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_frequency"
    assert (state := hass.states.get(entity_id))
    assert state.state == "208.0"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfFrequency.HERTZ
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:2-counter_frequency"

    entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_frequency_value"
    assert (state := hass.states.get(entity_id))
    assert state.state == "6.11"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == expected_unit

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:2-counter_frequency_value"