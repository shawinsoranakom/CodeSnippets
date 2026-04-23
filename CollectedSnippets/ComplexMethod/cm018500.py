async def test_rpc_analog_input_sensors(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
    original_unit: str | None,
    expected_unit: str | None,
) -> None:
    """Test RPC analog input xpercent sensor."""
    config = deepcopy(mock_rpc_device.config)
    config["input:1"]["xpercent"] = {"expr": "x*0.2995", "unit": original_unit}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    await init_integration(hass, 2)

    entity_id = f"{SENSOR_DOMAIN}.test_name_input_1_analog"
    assert (state := hass.states.get(entity_id))
    assert state.state == "89"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:1-analoginput"

    entity_id = f"{SENSOR_DOMAIN}.test_name_input_1_analog_value"
    assert (state := hass.states.get(entity_id))
    assert state.state == "8.9"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == expected_unit

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-input:1-analoginput_xpercent"