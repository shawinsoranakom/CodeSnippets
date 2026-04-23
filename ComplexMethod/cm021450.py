async def test_update_with_progress(
    hass: HomeAssistant, entity_id: str, steps: int
) -> None:
    """Test update with progress."""
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_IN_PROGRESS] is False
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    events = []
    async_track_state_change_event(
        hass,
        entity_id,
        # pylint: disable-next=unnecessary-lambda
        callback(lambda event: events.append(event)),
    )

    with patch("homeassistant.components.demo.update.FAKE_INSTALL_SLEEP_TIME", new=0):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert len(events) == steps + 1
    for i, event in enumerate(events[:steps]):
        new_state = event.data["new_state"]
        assert new_state.state == STATE_ON
        assert new_state.attributes[ATTR_UPDATE_PERCENTAGE] == pytest.approx(
            100 / steps * i
        )
    new_state = events[steps].data["new_state"]
    assert new_state.attributes[ATTR_IN_PROGRESS] is False
    assert new_state.attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert new_state.state == STATE_OFF