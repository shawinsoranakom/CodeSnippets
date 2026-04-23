async def test_volume_maximum(
    hass: HomeAssistant,
    controller: EcovacsController,
) -> None:
    """Test volume maximum."""
    device = controller.devices[0]
    event_bus = device.events
    entity_id = "number.ozmo_950_volume"
    assert (state := hass.states.get(entity_id))
    assert state.attributes["max"] == 10

    event_bus.notify(VolumeEvent(5, 20))
    await block_till_done(hass, event_bus)
    assert (state := hass.states.get(entity_id))
    assert state.state == "5"
    assert state.attributes["max"] == 20

    event_bus.notify(VolumeEvent(10, None))
    await block_till_done(hass, event_bus)
    assert (state := hass.states.get(entity_id))
    assert state.state == "10"
    assert state.attributes["max"] == 20