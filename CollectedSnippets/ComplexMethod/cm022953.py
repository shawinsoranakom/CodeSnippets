async def test_loading_switch(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    dummy_device_from_host_switch,
) -> None:
    """Test the WiLight configuration entry loading."""

    entry = await setup_integration(hass)
    assert entry
    assert entry.unique_id == WILIGHT_ID

    # First segment of the strip
    state = hass.states.get("switch.wl000000000099_1_watering")
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get("switch.wl000000000099_1_watering")
    assert entry
    assert entry.unique_id == "WL000000000099_0"

    # Seconnd segment of the strip
    state = hass.states.get("switch.wl000000000099_2_pause")
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get("switch.wl000000000099_2_pause")
    assert entry
    assert entry.unique_id == "WL000000000099_1"