async def test_saving_state_and_removing_entity(
    hass: HomeAssistant,
    setup_recorder: None,
) -> None:
    """Test saving the state of a removed entity."""
    entity_id = "lock.mine"
    hass.states.async_set(entity_id, LockState.LOCKED)
    hass.states.async_set(entity_id, LockState.UNLOCKED)
    hass.states.async_remove(entity_id)

    await async_wait_recording_done(hass)

    with session_scope(hass=hass, read_only=True) as session:
        states = list(
            session.query(StatesMeta.entity_id, States.state)
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
            .order_by(States.last_updated_ts)
        )
        assert len(states) == 3
        assert states[0].entity_id == entity_id
        assert states[0].state == LockState.LOCKED
        assert states[1].entity_id == entity_id
        assert states[1].state == LockState.UNLOCKED
        assert states[2].entity_id == entity_id
        assert states[2].state is None