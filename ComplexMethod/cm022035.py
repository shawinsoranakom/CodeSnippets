async def test_grid_migration_more_imports_than_exports(hass: HomeAssistant) -> None:
    """Test migration with 3 imports + 1 export creates 3 grids (first has export)."""
    old_data = {
        "energy_sources": [
            {
                "type": "grid",
                "flow_from": [
                    {"stat_energy_from": "sensor.import_1"},
                    {"stat_energy_from": "sensor.import_2"},
                    {"stat_energy_from": "sensor.import_3"},
                ],
                "flow_to": [
                    {"stat_energy_to": "sensor.export_1"},
                ],
                "cost_adjustment_day": 0,
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
    assert len(manager.data["energy_sources"]) == 3

    # First grid: has both import and export
    grid1 = manager.data["energy_sources"][0]
    assert grid1["stat_energy_from"] == "sensor.import_1"
    assert grid1["stat_energy_to"] == "sensor.export_1"

    # Second and third grids: import only
    grid2 = manager.data["energy_sources"][1]
    assert grid2["stat_energy_from"] == "sensor.import_2"
    assert grid2["stat_energy_to"] is None

    grid3 = manager.data["energy_sources"][2]
    assert grid3["stat_energy_from"] == "sensor.import_3"
    assert grid3["stat_energy_to"] is None