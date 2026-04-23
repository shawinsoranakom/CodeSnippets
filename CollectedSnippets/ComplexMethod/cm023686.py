async def test_purge_entities(hass: HomeAssistant, recorder_mock: Recorder) -> None:
    """Test purging of specific entities."""

    async def _purge_entities(
        hass: HomeAssistant, entity_ids: str, domains: str, entity_globs: str
    ) -> None:
        service_data = {
            "entity_id": entity_ids,
            "domains": domains,
            "entity_globs": entity_globs,
        }

        await hass.services.async_call(DOMAIN, SERVICE_PURGE_ENTITIES, service_data)
        await hass.async_block_till_done()

        await async_recorder_block_till_done(hass)
        await async_wait_purge_done(hass)

    def _add_purge_records(hass: HomeAssistant) -> None:
        with session_scope(hass=hass) as session:
            # Add states and state_changed events that should be purged
            for days in range(1, 4):
                timestamp = dt_util.utcnow() - timedelta(days=days)
                for event_id in range(1000, 1020):
                    _add_state_with_state_attributes(
                        session,
                        "sensor.purge_entity",
                        "purgeme",
                        timestamp,
                        event_id * days,
                    )
                timestamp = dt_util.utcnow() - timedelta(days=days)
                for event_id in range(10000, 10020):
                    _add_state_with_state_attributes(
                        session,
                        "purge_domain.entity",
                        "purgeme",
                        timestamp,
                        event_id * days,
                    )
                timestamp = dt_util.utcnow() - timedelta(days=days)
                for event_id in range(100000, 100020):
                    _add_state_with_state_attributes(
                        session,
                        "binary_sensor.purge_glob",
                        "purgeme",
                        timestamp,
                        event_id * days,
                    )
            convert_pending_states_to_meta(recorder_mock, session)
            convert_pending_events_to_event_types(recorder_mock, session)

    def _add_keep_records(hass: HomeAssistant) -> None:
        with session_scope(hass=hass) as session:
            # Add states and state_changed events that should be kept
            timestamp = dt_util.utcnow() - timedelta(days=2)
            for event_id in range(200, 210):
                _add_state_with_state_attributes(
                    session,
                    "sensor.keep",
                    "keep",
                    timestamp,
                    event_id,
                )
            convert_pending_states_to_meta(recorder_mock, session)
            convert_pending_events_to_event_types(recorder_mock, session)

    _add_purge_records(hass)
    _add_keep_records(hass)

    # Confirm standard service call
    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 190

    await _purge_entities(hass, "sensor.purge_entity", "purge_domain", "*purge_glob")

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 10

        states_sensor_kept = (
            session.query(States)
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
            .filter(StatesMeta.entity_id == "sensor.keep")
        )
        assert states_sensor_kept.count() == 10

    _add_purge_records(hass)

    # Confirm each parameter purges only the associated records
    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 190

    await _purge_entities(hass, "sensor.purge_entity", [], [])

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 130

    await _purge_entities(hass, [], "purge_domain", [])

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 70

    await _purge_entities(hass, [], [], "*purge_glob")

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 10

        states_sensor_kept = (
            session.query(States)
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
            .filter(StatesMeta.entity_id == "sensor.keep")
        )
        assert states_sensor_kept.count() == 10

        # sensor.keep should remain in the StatesMeta table
        states_meta_remain = session.query(StatesMeta).filter(
            StatesMeta.entity_id == "sensor.keep"
        )
        assert states_meta_remain.count() == 1

        # sensor.purge_entity should be removed from the StatesMeta table
        states_meta_remain = session.query(StatesMeta).filter(
            StatesMeta.entity_id == "sensor.purge_entity"
        )
        assert states_meta_remain.count() == 0

    _add_purge_records(hass)

    # Confirm calling service without arguments is invalid
    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 190

    with pytest.raises(MultipleInvalid):
        await _purge_entities(hass, [], [], [])

    with session_scope(hass=hass, read_only=True) as session:
        states = session.query(States)
        assert states.count() == 190

        states_meta_remain = session.query(StatesMeta)
        assert states_meta_remain.count() == 4