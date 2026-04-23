async def test_purge_cutoff_date(hass: HomeAssistant, recorder_mock: Recorder) -> None:
    """Test states and events are purged only if they occurred before "now() - keep_days"."""

    async def _add_db_entries(hass: HomeAssistant, cutoff: datetime, rows: int) -> None:
        timestamp_keep = cutoff
        timestamp_purge = cutoff - timedelta(microseconds=1)

        with session_scope(hass=hass) as session:
            session.add(
                Events(
                    event_id=1000,
                    event_type="KEEP",
                    event_data="{}",
                    origin="LOCAL",
                    time_fired_ts=timestamp_keep.timestamp(),
                )
            )
            session.add(
                States(
                    entity_id="test.cutoff",
                    state="keep",
                    attributes="{}",
                    last_changed_ts=timestamp_keep.timestamp(),
                    last_updated_ts=timestamp_keep.timestamp(),
                    event_id=1000,
                    attributes_id=1000,
                )
            )
            session.add(
                StateAttributes(
                    shared_attrs="{}",
                    hash=1234,
                    attributes_id=1000,
                )
            )
            for row in range(1, rows):
                session.add(
                    Events(
                        event_id=1000 + row,
                        event_type="PURGE",
                        event_data="{}",
                        origin="LOCAL",
                        time_fired_ts=timestamp_purge.timestamp(),
                    )
                )
                session.add(
                    States(
                        entity_id="test.cutoff",
                        state="purge",
                        attributes="{}",
                        last_changed_ts=timestamp_purge.timestamp(),
                        last_updated_ts=timestamp_purge.timestamp(),
                        event_id=1000 + row,
                        attributes_id=1000 + row,
                    )
                )
                session.add(
                    StateAttributes(
                        shared_attrs="{}",
                        hash=1234,
                        attributes_id=1000 + row,
                    )
                )

    await async_attach_db_engine(hass)

    await async_wait_purge_done(hass)

    service_data = {"keep_days": 2}

    # Force multiple purge batches to be run
    rows = 999
    cutoff = dt_util.utcnow() - timedelta(days=service_data["keep_days"])
    await _add_db_entries(hass, cutoff, rows)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        events = session.query(Events)
        assert states.filter(States.state == "purge").count() == rows - 1
        assert states.filter(States.state == "keep").count() == 1
        assert (
            state_attributes.outerjoin(
                States, StateAttributes.attributes_id == States.attributes_id
            )
            .filter(States.state == "keep")
            .count()
            == 1
        )
        assert events.filter(Events.event_type == "PURGE").count() == rows - 1
        assert events.filter(Events.event_type == "KEEP").count() == 1

    recorder_mock.queue_task(PurgeTask(cutoff, repack=False, apply_filter=False))
    await hass.async_block_till_done()
    await async_recorder_block_till_done(hass)
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        events = session.query(Events)
        assert states.filter(States.state == "purge").count() == 0
        assert (
            state_attributes.outerjoin(
                States, StateAttributes.attributes_id == States.attributes_id
            )
            .filter(States.state == "purge")
            .count()
            == 0
        )
        assert states.filter(States.state == "keep").count() == 1
        assert (
            state_attributes.outerjoin(
                States, StateAttributes.attributes_id == States.attributes_id
            )
            .filter(States.state == "keep")
            .count()
            == 1
        )
        assert events.filter(Events.event_type == "PURGE").count() == 0
        assert events.filter(Events.event_type == "KEEP").count() == 1

    # Make sure we can purge everything
    recorder_mock.queue_task(
        PurgeTask(dt_util.utcnow(), repack=False, apply_filter=False)
    )
    await async_recorder_block_till_done(hass)
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        assert states.count() == 0
        assert state_attributes.count() == 0

    # Make sure we can purge everything when the db is already empty
    recorder_mock.queue_task(
        PurgeTask(dt_util.utcnow(), repack=False, apply_filter=False)
    )
    await async_recorder_block_till_done(hass)
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        assert states.count() == 0
        assert state_attributes.count() == 0