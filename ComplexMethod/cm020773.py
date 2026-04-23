async def test_cover_set_position(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    entity_id: str,
    uid: str,
    name: str,
    model: str,
) -> None:
    """Test set position of the cover."""

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.CLOSED
    assert state.attributes.get("friendly_name") == name

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    with patch("homeassistant.components.freedompro.cover.put_state") as mock_put_state:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: [entity_id], ATTR_POSITION: 33},
            blocking=True,
        )
    mock_put_state.assert_called_once_with(ANY, ANY, ANY, '{"position": 33}')

    states_response = get_states_response_for_uid(uid)
    states_response[0]["state"]["position"] = 33
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes["current_position"] == 33