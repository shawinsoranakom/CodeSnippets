async def test_out_of_disk_space_while_rebuild_states_table(
    async_test_recorder: RecorderInstanceContextManager,
    caplog: pytest.LogCaptureFixture,
    recorder_db_url: str,
) -> None:
    """Test that we can recover from out of disk space while rebuilding the states table.

    This case tests the migration still happens if
    ix_states_event_id is removed from the states table.
    """
    importlib.import_module(SCHEMA_MODULE_32)
    old_db_schema = sys.modules[SCHEMA_MODULE_32]
    now = dt_util.utcnow()
    one_second_past = now - timedelta(seconds=1)
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

    def _get_event_id_foreign_keys():
        assert instance.engine is not None
        return next(
            (
                fk  # type: ignore[misc]
                for fk in inspect(instance.engine).get_foreign_keys("states")
                if fk["constrained_columns"] == ["event_id"]
            ),
            None,
        )

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
        patch.object(migration.EventIDPostMigration, "migrate_data"),
        patch.object(migration, "non_live_data_migration_needed", return_value=False),
        patch.object(migration, "post_migrate_entity_ids", return_value=False),
        patch.object(core, "StatesMeta", old_db_schema.StatesMeta),
        patch.object(core, "EventTypes", old_db_schema.EventTypes),
        patch.object(core, "EventData", old_db_schema.EventData),
        patch.object(core, "States", old_db_schema.States),
        patch.object(core, "Events", old_db_schema.Events),
        patch(
            CREATE_ENGINE_TARGET,
            new=_create_engine_test(
                SCHEMA_MODULE_32,
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

            await async_drop_index(instance, "states", "ix_states_event_id", caplog)

            states_indexes = await instance.async_add_executor_job(
                _get_states_index_names
            )
            states_index_names = {index["name"] for index in states_indexes}
            assert instance.use_legacy_events_index is True
            assert (
                await instance.async_add_executor_job(_get_event_id_foreign_keys)
                is not None
            )

            await hass.async_stop()
            await hass.async_block_till_done()

    assert "ix_states_entity_id_last_updated_ts" in states_index_names

    # Simulate out of disk space while rebuilding the states table by
    # - patching CreateTable to raise SQLAlchemyError for SQLite
    # - patching DropConstraint to raise InternalError for MySQL and PostgreSQL
    with (
        patch(
            "homeassistant.components.recorder.migration.CreateTable",
            side_effect=SQLAlchemyError,
        ),
        patch(
            "homeassistant.components.recorder.migration.DropConstraint",
            side_effect=OperationalError(
                None, None, OSError("No space left on device")
            ),
        ),
    ):
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

            states_indexes = await instance.async_add_executor_job(
                _get_states_index_names
            )
            states_index_names = {index["name"] for index in states_indexes}
            assert instance.use_legacy_events_index is True
            assert "Error recreating SQLite table states" in caplog.text
            assert await instance.async_add_executor_job(_get_event_id_foreign_keys)

            await hass.async_stop()

    # Now run it again to verify the table rebuild tries again
    caplog.clear()
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

        states_indexes = await instance.async_add_executor_job(_get_states_index_names)
        states_index_names = {index["name"] for index in states_indexes}
        assert instance.use_legacy_events_index is False
        assert "ix_states_entity_id_last_updated_ts" not in states_index_names
        assert "ix_states_event_id" not in states_index_names
        assert "Rebuilding SQLite table states finished" in caplog.text
        assert await instance.async_add_executor_job(_get_event_id_foreign_keys) is None

        await hass.async_stop()