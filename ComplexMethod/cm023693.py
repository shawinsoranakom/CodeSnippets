async def test_get_full_significant_states_handles_empty_last_changed(
    hass: HomeAssistant,
) -> None:
    """Test getting states when last_changed is null."""
    now = dt_util.utcnow()
    hass.states.async_set("sensor.one", "on", {"attr": "original"})
    state0 = hass.states.get("sensor.one")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.one", "on", {"attr": "new"})
    state1 = hass.states.get("sensor.one")

    assert state0.last_changed == state1.last_changed
    assert state0.last_updated != state1.last_updated
    await async_wait_recording_done(hass)

    def _get_entries():
        with session_scope(hass=hass, read_only=True) as session:
            return history.get_full_significant_states_with_session(
                hass,
                session,
                now,
                dt_util.utcnow(),
                entity_ids=["sensor.one"],
                significant_changes_only=False,
            )

    states = await recorder.get_instance(hass).async_add_executor_job(_get_entries)
    sensor_one_states: list[State] = states["sensor.one"]
    assert_states_equal_without_context(sensor_one_states[0], state0)
    assert_states_equal_without_context(sensor_one_states[1], state1)
    assert sensor_one_states[0].last_changed == sensor_one_states[1].last_changed
    assert sensor_one_states[0].last_updated != sensor_one_states[1].last_updated

    def _fetch_native_states() -> list[State]:
        with session_scope(hass=hass, read_only=True) as session:
            native_states = []
            db_state_attributes = {
                state_attributes.attributes_id: state_attributes
                for state_attributes in session.query(StateAttributes)
            }
            metadata_id_to_entity_id = {
                states_meta.metadata_id: states_meta
                for states_meta in session.query(StatesMeta)
            }
            for db_state in session.query(States):
                db_state.entity_id = metadata_id_to_entity_id[
                    db_state.metadata_id
                ].entity_id
                state = db_state_to_native(db_state)
                state.attributes = db_state_attributes_to_native(
                    db_state_attributes[db_state.attributes_id]
                )
                native_states.append(state)
            return native_states

    native_sensor_one_states = await recorder.get_instance(hass).async_add_executor_job(
        _fetch_native_states
    )
    assert_states_equal_without_context(native_sensor_one_states[0], state0)
    assert_states_equal_without_context(native_sensor_one_states[1], state1)
    assert (
        native_sensor_one_states[0].last_changed
        == native_sensor_one_states[1].last_changed
    )
    assert (
        native_sensor_one_states[0].last_updated
        != native_sensor_one_states[1].last_updated
    )

    def _fetch_db_states() -> list[States]:
        with session_scope(hass=hass, read_only=True) as session:
            states = list(session.query(States))
            session.expunge_all()
            return states

    db_sensor_one_states = await recorder.get_instance(hass).async_add_executor_job(
        _fetch_db_states
    )
    assert db_sensor_one_states[0].last_changed is None
    assert db_sensor_one_states[0].last_changed_ts is None

    assert (
        process_timestamp(
            dt_util.utc_from_timestamp(db_sensor_one_states[1].last_changed_ts)
        )
        == state0.last_changed
    )
    assert db_sensor_one_states[0].last_updated_ts is not None
    assert db_sensor_one_states[1].last_updated_ts is not None
    assert (
        db_sensor_one_states[0].last_updated_ts
        != db_sensor_one_states[1].last_updated_ts
    )