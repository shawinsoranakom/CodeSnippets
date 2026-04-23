async def test_purge_old_states_purges_the_state_metadata_ids(
    hass: HomeAssistant, recorder_mock: Recorder
) -> None:
    """Test deleting old states purges state metadata_ids."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)
    far_past = utcnow - timedelta(days=1000)

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    def _insert_states():
        with session_scope(hass=hass) as session:
            states_meta_sensor_one = StatesMeta(entity_id="sensor.one")
            states_meta_sensor_two = StatesMeta(entity_id="sensor.two")
            states_meta_sensor_three = StatesMeta(entity_id="sensor.three")
            states_meta_sensor_unused = StatesMeta(entity_id="sensor.unused")
            session.add_all(
                (
                    states_meta_sensor_one,
                    states_meta_sensor_two,
                    states_meta_sensor_three,
                    states_meta_sensor_unused,
                )
            )
            session.flush()
            for _ in range(5):
                for event_id in range(6):
                    if event_id < 2:
                        timestamp = eleven_days_ago
                        metadata_id = states_meta_sensor_one.metadata_id
                    elif event_id < 4:
                        timestamp = five_days_ago
                        metadata_id = states_meta_sensor_two.metadata_id
                    else:
                        timestamp = utcnow
                        metadata_id = states_meta_sensor_three.metadata_id

                    session.add(
                        States(
                            metadata_id=metadata_id,
                            state="any",
                            last_updated_ts=timestamp.timestamp(),
                        )
                    )
            return recorder_mock.states_meta_manager.get_many(
                ["sensor.one", "sensor.two", "sensor.three", "sensor.unused"],
                session,
                True,
            )

    entity_id_to_metadata_id = await recorder_mock.async_add_executor_job(
        _insert_states
    )
    test_metadata_ids = entity_id_to_metadata_id.values()
    with session_scope(hass=hass) as session:
        states = session.query(States).where(States.metadata_id.in_(test_metadata_ids))
        states_meta = session.query(StatesMeta).where(
            StatesMeta.metadata_id.in_(test_metadata_ids)
        )

        assert states.count() == 30
        assert states_meta.count() == 4

    # run purge_old_data()
    finished = purge_old_data(
        recorder_mock,
        far_past,
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        states = session.query(States).where(States.metadata_id.in_(test_metadata_ids))
        states_meta = session.query(StatesMeta).where(
            StatesMeta.metadata_id.in_(test_metadata_ids)
        )
        assert states.count() == 30
        # We should remove the unused entity_id
        assert states_meta.count() == 3

    assert "sensor.unused" not in recorder_mock.event_type_manager._id_map

    # we should only have 10 states left since
    # only one event type was recorded now
    finished = purge_old_data(
        recorder_mock,
        utcnow,
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        states = session.query(States).where(States.metadata_id.in_(test_metadata_ids))
        states_meta = session.query(StatesMeta).where(
            StatesMeta.metadata_id.in_(test_metadata_ids)
        )
        assert states.count() == 10
        assert states_meta.count() == 1

    # Purge everything
    finished = purge_old_data(
        recorder_mock,
        utcnow + timedelta(seconds=1),
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        states = session.query(States).where(States.metadata_id.in_(test_metadata_ids))
        states_meta = session.query(StatesMeta).where(
            StatesMeta.metadata_id.in_(test_metadata_ids)
        )
        assert states.count() == 0
        assert states_meta.count() == 0