async def test_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    entity_ids: list[str],
) -> None:
    """Test that sensor entity snapshots match."""
    for entity_id in entity_ids:
        assert (state := hass.states.get(entity_id))
        assert snapshot(name=f"{entity_id}:state") == state

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert snapshot(name=f"{entity_id}:device-registry") == device_entry