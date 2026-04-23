async def test_grid_migration_power_only(hass: HomeAssistant) -> None:
    """Test migration with only power configured (no import/export meters)."""
    old_data = {
        "energy_sources": [
            {
                "type": "grid",
                "flow_from": [],
                "flow_to": [],
                "power": [
                    {"stat_rate": "sensor.grid_power"},
                ],
                "cost_adjustment_day": 0.5,
            }
        ],
        "device_consumption": [],
        "device_consumption_water": [],
    }

    old_store = storage.Store(hass, 1, "energy", minor_version=2)
    await old_store.async_save(old_data)

    manager = EnergyManager(hass)
    await manager.async_initialize()

    assert manager.data is not None
    assert len(manager.data["energy_sources"]) == 1

    grid = manager.data["energy_sources"][0]
    assert grid["type"] == "grid"
    # No import or export meters
    assert grid["stat_energy_from"] is None
    assert grid["stat_energy_to"] is None
    # Power is preserved
    assert grid["stat_rate"] == "sensor.grid_power"
    assert grid["cost_adjustment_day"] == 0.5