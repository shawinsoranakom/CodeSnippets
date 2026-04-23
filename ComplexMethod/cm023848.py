async def test_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test the Twente Milieu waste pickup sensors."""
    assert (state := hass.states.get(entity_id))
    assert state == snapshot

    assert (entity_entry := entity_registry.async_get(state.entity_id))
    assert entity_entry == snapshot

    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert device_entry == snapshot