async def test_light_state_temperature(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the creation and values of the Elgato Lights in temperature mode."""

    # First segment of the strip
    assert (state := hass.states.get("light.frenck"))
    assert state == snapshot

    assert (entry := entity_registry.async_get("light.frenck"))
    assert entry == snapshot

    assert entry.device_id
    assert (device_entry := device_registry.async_get(entry.device_id))
    assert device_entry == snapshot