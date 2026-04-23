async def test_rpc_rgbw_sensors(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    light_type: str,
) -> None:
    """Test sensors for RGB/RGBW light."""
    config = deepcopy(mock_rpc_device.config)
    config[f"{light_type}:0"] = {"id": 0}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status[f"{light_type}:0"] = {
        "temperature": {"tC": 54.3, "tF": 129.7},
        "aenergy": {"total": 45.141},
        "apower": 12.2,
        "current": 0.23,
        "voltage": 12.4,
    }
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 2)

    entity_id = f"sensor.test_name_{light_type}_light_0_power"

    assert (state := hass.states.get(entity_id))
    assert state.state == "12.2"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{light_type}:0-power_{light_type}"

    entity_id = f"sensor.test_name_{light_type}_light_0_energy"

    assert (state := hass.states.get(entity_id))
    assert state.state == "0.045141"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{light_type}:0-energy_{light_type}"

    entity_id = f"sensor.test_name_{light_type}_light_0_current"

    assert (state := hass.states.get(entity_id))
    assert state.state == "0.23"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfElectricCurrent.AMPERE
    )

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{light_type}:0-current_{light_type}"

    entity_id = f"sensor.test_name_{light_type}_light_0_voltage"

    assert (state := hass.states.get(entity_id))
    assert state.state == "12.4"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfElectricPotential.VOLT
    )

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{light_type}:0-voltage_{light_type}"

    entity_id = f"sensor.test_name_{light_type}_light_0_temperature"

    assert (state := hass.states.get(entity_id))
    assert state.state == "54.3"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{light_type}:0-temperature_{light_type}"