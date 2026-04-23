async def test_grid_migration_single_import_export(hass: HomeAssistant) -> None:
    """Test migration from legacy format with 1 import + 1 export creates 1 grid."""
    # Create legacy format data (v1.2) with flow_from/flow_to arrays
    old_data = {
        "energy_sources": [
            {
                "type": "grid",
                "flow_from": [
                    {
                        "stat_energy_from": "sensor.grid_import",
                        "stat_cost": "sensor.grid_cost",
                        "entity_energy_price": None,
                        "number_energy_price": None,
                    }
                ],
                "flow_to": [
                    {
                        "stat_energy_to": "sensor.grid_export",
                        "stat_compensation": None,
                        "entity_energy_price": "sensor.sell_price",
                        "number_energy_price": None,
                    }
                ],
                "cost_adjustment_day": 0.5,
            }
        ],
        "device_consumption": [],
        "device_consumption_water": [],
    }

    # Save with old version (1.2) - migration will run to upgrade to 1.3
    old_store = storage.Store(hass, 1, "energy", minor_version=2)
    await old_store.async_save(old_data)

    # Load with manager - should trigger migration
    manager = EnergyManager(hass)
    await manager.async_initialize()

    # Verify migration created unified grid source
    assert manager.data is not None
    assert len(manager.data["energy_sources"]) == 1

    grid = manager.data["energy_sources"][0]
    assert grid["type"] == "grid"
    assert grid["stat_energy_from"] == "sensor.grid_import"
    assert grid["stat_energy_to"] == "sensor.grid_export"
    assert grid["stat_cost"] == "sensor.grid_cost"
    assert grid["stat_compensation"] is None
    assert grid["entity_energy_price"] is None
    assert grid["entity_energy_price_export"] == "sensor.sell_price"
    assert grid["cost_adjustment_day"] == 0.5

    # Should not have legacy fields
    assert "flow_from" not in grid
    assert "flow_to" not in grid