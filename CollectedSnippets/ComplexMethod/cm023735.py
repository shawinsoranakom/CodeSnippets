async def test_post_migrate_entity_ids(
    async_test_recorder: RecorderInstanceContextManager,
    indices_to_drop: list[tuple[str, str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we can migrate entity_ids to the StatesMeta table."""
    importlib.import_module(SCHEMA_MODULE_32)
    old_db_schema = sys.modules[SCHEMA_MODULE_32]

    def _insert_events():
        with session_scope(hass=hass) as session:
            session.add_all(
                (
                    old_db_schema.States(
                        entity_id="sensor.one",
                        state="one_1",
                        last_updated_ts=1.452529,
                    ),
                    old_db_schema.States(
                        entity_id="sensor.two",
                        state="two_2",
                        last_updated_ts=2.252529,
                    ),
                    old_db_schema.States(
                        entity_id="sensor.two",
                        state="two_1",
                        last_updated_ts=3.152529,
                    ),
                )
            )

    # Create database with old schema
    with (
        patch.object(recorder, "db_schema", old_db_schema),
        patch.object(migration, "SCHEMA_VERSION", old_db_schema.SCHEMA_VERSION),
        patch.object(
            migration,
            "LIVE_MIGRATION_MIN_SCHEMA_VERSION",
            get_patched_live_version(old_db_schema),
        ),
        patch.object(migration.EntityIDMigration, "migrate_data"),
        patch.object(migration.EntityIDPostMigration, "migrate_data"),
        patch(CREATE_ENGINE_TARGET, new=_create_engine_test),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await instance.async_add_executor_job(_insert_events)

            await async_wait_recording_done(hass)
            await _async_wait_migration_done(hass)

            # Remove index
            instance.recorder_and_worker_thread_ids.add(threading.get_ident())
            for table, index in indices_to_drop:
                with session_scope(hass=hass) as session:
                    assert get_index_by_name(session, table, index) is not None
                await async_drop_index(instance, table, index, caplog)

            await hass.async_stop()
            await hass.async_block_till_done()

    def _fetch_migrated_states():
        with session_scope(hass=hass, read_only=True) as session:
            states = session.query(
                States.state,
                States.entity_id,
            ).all()
            assert len(states) == 3
            return {state.state: state.entity_id for state in states}

    # Run again with new schema, let migration run
    async with async_test_home_assistant() as hass:
        with (
            instrument_migration(hass) as instrumented_migration,
            patch(
                "sqlalchemy.schema.Index.create", autospec=True, wraps=Index.create
            ) as wrapped_idx_create,
        ):
            # Stall migration when the last non-live schema migration is done
            instrumented_migration.stall_on_schema_version = (
                migration.LIVE_MIGRATION_MIN_SCHEMA_VERSION
            )
            async with async_test_recorder(
                hass, wait_recorder=False, wait_recorder_setup=False
            ) as instance:
                # Wait for non-live schema migration to complete
                await hass.async_add_executor_job(
                    instrumented_migration.apply_update_stalled.wait
                )
                wrapped_idx_create.reset_mock()
                instrumented_migration.migration_stall.set()

                instance.recorder_and_worker_thread_ids.add(threading.get_ident())

                await hass.async_block_till_done()
                await async_wait_recording_done(hass)
                await async_wait_recording_done(hass)

                states_by_state = await instance.async_add_executor_job(
                    _fetch_migrated_states
                )

                # Check the index which will be removed by the migrator no longer exists
                with session_scope(hass=hass) as session:
                    assert (
                        get_index_by_name(
                            session, "states", "ix_states_entity_id_last_updated_ts"
                        )
                        is None
                    )

                await hass.async_stop()
                await hass.async_block_till_done()

    # Check the index we removed was recreated
    index_names = [call[1][0].name for call in wrapped_idx_create.mock_calls]
    assert index_names == [index for _, index in indices_to_drop]

    assert states_by_state["one_1"] is None
    assert states_by_state["two_2"] is None
    assert states_by_state["two_1"] is None