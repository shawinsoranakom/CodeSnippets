async def test_grid_migration_multiple_imports_exports_paired(
    hass: HomeAssistant,
) -> None:
    """Test migration with 2 imports + 2 exports creates 2 paired grids."""
    old_data = {
        "energy_sources": [
            {
                "type": "grid",
                "flow_from": [
                    {
                        "stat_energy_from": "sensor.grid_import_1",
                        "stat_cost": None,
                        "entity_energy_price": None,
                        "number_energy_price": 0.15,
                    },
                    {
                        "stat_energy_from": "sensor.grid_import_2",
                        "stat_cost": None,
                        "entity_energy_price": None,
                        "number_energy_price": 0.20,
                    },
                ],
                "flow_to": [
                    {
                        "stat_energy_to": "sensor.grid_export_1",
                        "stat_compensation": None,
                        "entity_energy_price": None,
                        "number_energy_price": 0.08,
                    },
                    {
                        "stat_energy_to": "sensor.grid_export_2",
                        "stat_compensation": None,
                        "entity_energy_price": None,
                        "number_energy_price": 0.05,
                    },
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
    assert len(manager.data["energy_sources"]) == 2

    # First grid: paired import_1 with export_1
    grid1 = manager.data["energy_sources"][0]
    assert grid1["stat_energy_from"] == "sensor.grid_import_1"
    assert grid1["stat_energy_to"] == "sensor.grid_export_1"
    assert grid1["number_energy_price"] == 0.15
    assert grid1["number_energy_price_export"] == 0.08

    # Second grid: paired import_2 with export_2
    grid2 = manager.data["energy_sources"][1]
    assert grid2["stat_energy_from"] == "sensor.grid_import_2"
    assert grid2["stat_energy_to"] == "sensor.grid_export_2"
    assert grid2["number_energy_price"] == 0.20
    assert grid2["number_energy_price_export"] == 0.05