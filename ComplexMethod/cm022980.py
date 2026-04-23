async def test_mop_attached(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    controller: EcovacsController,
) -> None:
    """Test mop_attached binary sensor."""
    entity_id = "binary_sensor.ozmo_950_mop_attached"
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNKNOWN

    assert (entity_entry := entity_registry.async_get(state.entity_id))
    assert entity_entry == snapshot(name=f"{entity_id}-entity_entry")
    assert entity_entry.device_id

    device = controller.devices[0]

    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert device_entry.identifiers == {(DOMAIN, device.device_info["did"])}

    event_bus = device.events
    await notify_and_wait(hass, event_bus, MopAttachedEvent(True))

    assert (state := hass.states.get(state.entity_id))
    assert state == snapshot(name=f"{entity_id}-state")

    await notify_and_wait(hass, event_bus, MopAttachedEvent(False))

    assert (state := hass.states.get(state.entity_id))
    assert state.state == STATE_OFF