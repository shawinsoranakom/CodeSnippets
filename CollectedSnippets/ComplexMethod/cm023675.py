async def test_migrate_times(
    async_test_recorder: RecorderInstanceContextManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we can migrate times in the events and states tables.

    Also tests entity id post migration.
    """
    importlib.import_module(SCHEMA_MODULE_30)
    old_db_schema = sys.modules[SCHEMA_MODULE_30]
    now = dt_util.utcnow()
    one_second_past = now - timedelta(seconds=1)
    now_timestamp = now.timestamp()
    one_second_past_timestamp = one_second_past.timestamp()

    mock_state = State(
        "sensor.test",
        "old",
        {"last_reset": now.isoformat()},
        last_changed=one_second_past,
        last_updated=now,
    )
    state_changed_event = Event(
        EVENT_STATE_CHANGED,
        {
            "entity_id": "sensor.test",
            "old_state": None,
            "new_state": mock_state,
        },
        EventOrigin.local,
        time_fired_timestamp=now.timestamp(),
    )
    custom_event = Event(
        "custom_event",
        {"entity_id": "sensor.custom"},
        EventOrigin.local,
        time_fired_timestamp=now.timestamp(),
    )
    number_of_migrations = 5

    def _get_states_index_names():
        with session_scope(hass=hass) as session:
            return inspect(session.connection()).get_indexes("states")

    with (
        patch.object(recorder, "db_schema", old_db_schema),
        patch.object(migration, "SCHEMA_VERSION", old_db_schema.SCHEMA_VERSION),
        patch.object(
            migration,
            "LIVE_MIGRATION_MIN_SCHEMA_VERSION",
            get_patched_live_version(old_db_schema),
        ),
        patch.object(migration, "non_live_data_migration_needed", return_value=False),
        patch.object(migration, "post_migrate_entity_ids", return_value=False),
        patch.object(migration.EventsContextIDMigration, "migrate_data"),
        patch.object(migration.StatesContextIDMigration, "migrate_data"),
        patch.object(migration.EventTypeIDMigration, "migrate_data"),
        patch.object(migration.EntityIDMigration, "migrate_data"),
        patch.object(migration.EventIDPostMigration, "migrate_data"),
        patch.object(core, "StatesMeta", old_db_schema.StatesMeta),
        patch.object(core, "EventTypes", old_db_schema.EventTypes),
        patch.object(core, "EventData", old_db_schema.EventData),
        patch.object(core, "States", old_db_schema.States),
        patch.object(core, "Events", old_db_schema.Events),
        patch(
            CREATE_ENGINE_TARGET,
            new=_create_engine_test(
                SCHEMA_MODULE_30,
                initial_version=27,  # Set to 27 for the entity id post migration to run
            ),
        ),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await hass.async_block_till_done()
            await async_wait_recording_done(hass)
            await async_wait_recording_done(hass)

            def _add_data():
                with session_scope(hass=hass) as session:
                    session.add(old_db_schema.Events.from_event(custom_event))
                    session.add(old_db_schema.States.from_event(state_changed_event))

            await instance.async_add_executor_job(_add_data)
            await hass.async_block_till_done()
            await instance.async_block_till_done()

            states_indexes = await instance.async_add_executor_job(
                _get_states_index_names
            )
            states_index_names = {index["name"] for index in states_indexes}
            assert instance.use_legacy_events_index is True

            await hass.async_stop()
            await hass.async_block_till_done()

    assert "ix_states_event_id" in states_index_names

    # Test that the duplicates are removed during migration from schema 23
    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass) as instance,
    ):
        await hass.async_block_till_done()

        # We need to wait for all the migration tasks to complete
        # before we can check the database.
        for _ in range(number_of_migrations):
            await instance.async_block_till_done()
            await async_wait_recording_done(hass)

        def _get_test_data_from_db():
            with session_scope(hass=hass) as session:
                events_result = list(
                    session.query(recorder.db_schema.Events).filter(
                        recorder.db_schema.Events.event_type_id.in_(
                            select_event_type_ids(("custom_event",))
                        )
                    )
                )
                states_result = list(
                    session.query(recorder.db_schema.States)
                    .join(
                        recorder.db_schema.StatesMeta,
                        recorder.db_schema.States.metadata_id
                        == recorder.db_schema.StatesMeta.metadata_id,
                    )
                    .where(recorder.db_schema.StatesMeta.entity_id == "sensor.test")
                )
                session.expunge_all()
                return events_result, states_result

        events_result, states_result = await instance.async_add_executor_job(
            _get_test_data_from_db
        )

        assert len(events_result) == 1
        assert events_result[0].time_fired_ts == now_timestamp
        assert events_result[0].time_fired is None
        assert len(states_result) == 1
        assert states_result[0].last_changed_ts == one_second_past_timestamp
        assert states_result[0].last_updated_ts == now_timestamp
        assert states_result[0].last_changed is None
        assert states_result[0].last_updated is None

        def _get_events_index_names():
            with session_scope(hass=hass) as session:
                return inspect(session.connection()).get_indexes("events")

        events_indexes = await instance.async_add_executor_job(_get_events_index_names)
        events_index_names = {index["name"] for index in events_indexes}

        assert "ix_events_context_id_bin" in events_index_names
        assert "ix_events_context_id" not in events_index_names

        states_indexes = await instance.async_add_executor_job(_get_states_index_names)
        states_index_names = {index["name"] for index in states_indexes}

        # sqlite does not support dropping foreign keys so we had to
        # create a new table and copy the data over
        assert "ix_states_event_id" not in states_index_names

        assert instance.use_legacy_events_index is False

        await hass.async_stop()