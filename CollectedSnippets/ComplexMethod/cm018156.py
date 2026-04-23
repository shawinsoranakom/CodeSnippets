async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
) -> None:
    """Test the underlying sensors."""
    await init_integration(
        hass, config_entry, "sensor", DEFAULT_CHARGE_POINT, charge_point_status, grid
    )

    for entity_id, key in charge_point_entity_ids.items():
        entry = entity_registry.async_get(f"sensor.101_{entity_id}")
        assert entry
        assert entry.unique_id == f"{key}_101"

        state = hass.states.get(f"sensor.101_{entity_id}")
        assert state is not None

        value = charge_point_status[key]
        assert state.state == str(value)

    for entity_id, key in grid_entity_ids.items():
        entry = entity_registry.async_get(f"sensor.{entity_id}")
        assert entry
        assert entry.unique_id == key

        state = hass.states.get(f"sensor.{entity_id}")
        assert state is not None
        assert state.state == str(grid[key])