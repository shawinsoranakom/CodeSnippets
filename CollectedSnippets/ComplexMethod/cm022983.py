async def test_legacy_sensors(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_vacbot: Mock,
) -> None:
    """Test that sensor entity snapshots match."""
    mock_vacbot.components = {"main_brush": 0.8, "side_brush": 0.6, "filter": 0.4}
    mock_vacbot.lifespanEvents.notify("dummy_data")
    await hass.async_block_till_done(wait_background_tasks=True)

    states = hass.states.async_entity_ids()
    assert snapshot(name="states") == states

    for entity_id in hass.states.async_entity_ids():
        assert (state := hass.states.get(entity_id)), f"State of {entity_id} is missing"
        assert snapshot(name=f"{entity_id}:state") == state

        assert (entity_entry := entity_registry.async_get(state.entity_id))
        assert snapshot(name=f"{entity_id}:entity-registry") == entity_entry

        assert entity_entry.device_id
        assert (device_entry := device_registry.async_get(entity_entry.device_id))
        assert device_entry.identifiers == {(DOMAIN, "E1234567890000000003")}