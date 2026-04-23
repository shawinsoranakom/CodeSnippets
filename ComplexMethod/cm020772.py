async def test_cover_get_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
    entity_id: str,
    uid: str,
    name: str,
    model: str,
) -> None:
    """Test states of the cover."""

    device = device_registry.async_get_device(identifiers={("freedompro", uid)})
    assert device is not None
    assert device.identifiers == {("freedompro", uid)}
    assert device.manufacturer == "Freedompro"
    assert device.name == name
    assert device.model == model

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.CLOSED
    assert state.attributes.get("friendly_name") == name

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    states_response = get_states_response_for_uid(uid)
    states_response[0]["state"]["position"] = 100
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes.get("friendly_name") == name

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == uid

        assert state.state == CoverState.OPEN