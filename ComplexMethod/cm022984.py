async def test_selects(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    controller: EcovacsController,
    entity_ids: list[str],
) -> None:
    """Test that select entity snapshots match."""
    assert hass.states.async_entity_ids() == entity_ids
    for entity_id in entity_ids:
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert state.state == STATE_UNKNOWN

    device = controller.devices[0]
    await notify_events(hass, device.events)
    for entity_id in entity_ids:
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert snapshot(name=f"{entity_id}:state") == state

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert device_entry.identifiers == {(DOMAIN, device.device_info["did"])}