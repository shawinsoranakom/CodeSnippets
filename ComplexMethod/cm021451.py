async def test_update_with_progress_raising(
    hass: HomeAssistant, entity_id: str, steps: int
) -> None:
    """Test update with progress failing to install."""
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

    with (
        patch(
            "homeassistant.components.demo.update._fake_install",
            side_effect=[None, None, None, None, RuntimeError],
        ) as fake_sleep,
        pytest.raises(RuntimeError),
    ):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    await hass.async_block_till_done()

    assert fake_sleep.call_count == 5
    assert len(events) == 6
    for i, event in enumerate(events[:5]):
        new_state = event.data["new_state"]
        assert new_state.state == STATE_ON
        assert new_state.attributes[ATTR_UPDATE_PERCENTAGE] == pytest.approx(
            100 / steps * i
        )
    assert events[5].data["new_state"].attributes[ATTR_IN_PROGRESS] is False
    assert events[5].data["new_state"].attributes[ATTR_UPDATE_PERCENTAGE] is None
    assert events[5].data["new_state"].state == STATE_ON