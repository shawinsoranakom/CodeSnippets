async def test_rpc_rgbcct_sensors(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test sensors for RGBCCT light."""
    config = deepcopy(mock_rpc_device.config)
    config["rgbcct:0"] = {"id": 0}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["rgbcct:0"] = {
        "aenergy": {"total": 45.141},
        "apower": 12.2,
    }
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 2)

    entity_id = "sensor.test_name_power"

    assert (state := hass.states.get(entity_id))
    assert state.state == "12.2"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-rgbcct:0-power_rgbcct"
    assert entry.name is None
    assert entry.translation_key is None  # entity with device class and no channel name

    entity_id = "sensor.test_name_energy"

    assert (state := hass.states.get(entity_id))
    assert state.state == "0.045141"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-rgbcct:0-energy_rgbcct"
    assert entry.name is None
    assert entry.translation_key is None