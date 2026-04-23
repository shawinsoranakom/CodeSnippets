async def test_rpc_pulse_counter_sensors(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
    original_unit: str | None,
    expected_unit: str | None,
) -> None:
    """Test RPC counter sensor."""
    config = deepcopy(mock_rpc_device.config)
    config["input:2"]["xcounts"] = {"expr": "x/10", "unit": original_unit}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    await init_integration(hass, 2)

    entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter"
    assert (state := hass.states.get(entity_id))
    assert state.state == "56174"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "pulse"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:2-pulse_counter"

    entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_value"
    assert (state := hass.states.get(entity_id))
    assert state.state == "561.74"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == expected_unit

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:2-counter_value"