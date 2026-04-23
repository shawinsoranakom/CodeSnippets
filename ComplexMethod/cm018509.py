async def test_rpc_pm1_energy_consumed_sensor(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test energy sensors for switch component."""
    status = {
        "sys": {},
        "pm1:0": {
            "id": 0,
            "voltage": 235.0,
            "current": 0.957,
            "apower": -220.3,
            "freq": 50.0,
            "aenergy": {"total": 3000.000},
            "ret_aenergy": {"total": 1000.000},
        },
    }
    monkeypatch.setattr(mock_rpc_device, "status", status)
    await init_integration(hass, 3)

    assert (state := hass.states.get(f"{SENSOR_DOMAIN}.test_name_energy"))
    assert state.state == "3.0"

    assert (state := hass.states.get(f"{SENSOR_DOMAIN}.test_name_energy_returned"))
    assert state.state == "1.0"

    entity_id = f"{SENSOR_DOMAIN}.test_name_energy_consumed"
    # energy consumed = energy - energy returned
    assert (state := hass.states.get(entity_id))
    assert state.state == "2.0"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-pm1:0-consumed_energy_pm1"