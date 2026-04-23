async def test_cleanup_unmigrated_state_timestamps(
    async_test_recorder: RecorderInstanceContextManager,
) -> None:
    """Ensure schema 48 migration cleans up any unmigrated state timestamps."""
    importlib.import_module(SCHEMA_MODULE_32)
    old_db_schema = sys.modules[SCHEMA_MODULE_32]

    test_uuid = uuid.uuid4()
    uuid_hex = test_uuid.hex

    def _object_as_dict(obj):
        return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

    def _insert_states():
        with session_scope(hass=hass) as session:
            state1 = old_db_schema.States(
                entity_id="state.test_state1",
                last_updated=datetime.datetime(
                    2016, 10, 28, 20, 13, 52, 452529, tzinfo=datetime.UTC
                ),
                last_updated_ts=None,
                last_changed=datetime.datetime(
                    2016, 10, 28, 20, 13, 52, 452529, tzinfo=datetime.UTC
                ),
                last_changed_ts=None,
                context_id=uuid_hex,
                context_id_bin=None,
                context_user_id=None,
                context_user_id_bin=None,
                context_parent_id=None,
                context_parent_id_bin=None,
            )
            state2 = old_db_schema.States(
                entity_id="state.test_state2",
                last_updated=datetime.datetime(
                    2016, 10, 28, 20, 13, 52, 552529, tzinfo=datetime.UTC
                ),
                last_updated_ts=None,
                last_changed=datetime.datetime(
                    2016, 10, 28, 20, 13, 52, 452529, tzinfo=datetime.UTC
                ),
                last_changed_ts=None,
                context_id=None,
                context_id_bin=None,
                context_user_id=None,
                context_user_id_bin=None,
                context_parent_id=None,
                context_parent_id_bin=None,
            )
            session.add_all((state1, state2))
            # There is a default of now() for last_updated_ts so make sure it's not set
            session.query(old_db_schema.States).update(
                {old_db_schema.States.last_updated_ts: None}
            )
            state3 = old_db_schema.States(
                entity_id="state.already_migrated",
                last_updated=None,
                last_updated_ts=1477685632.452529,
                last_changed=None,
                last_changed_ts=1477685632.452529,
                context_id=uuid_hex,
                context_id_bin=None,
                context_user_id=None,
                context_user_id_bin=None,
                context_parent_id=None,
                context_parent_id_bin=None,
            )
            session.add_all((state3,))

        with session_scope(hass=hass, read_only=True) as session:
            states = session.query(old_db_schema.States).all()
            assert len(states) == 3

    # Create database with old schema
    with (
        patch.object(recorder, "db_schema", old_db_schema),
        patch.object(migration, "SCHEMA_VERSION", old_db_schema.SCHEMA_VERSION),
        patch.object(
            migration,
            "LIVE_MIGRATION_MIN_SCHEMA_VERSION",
            get_patched_live_version(old_db_schema),
        ),
        patch(CREATE_ENGINE_TARGET, new=_create_engine_test),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await instance.async_add_executor_job(_insert_states)

            await async_wait_recording_done(hass)
            await _async_wait_migration_done(hass)
            await async_wait_recording_done(hass)

            await hass.async_stop()
            await hass.async_block_till_done()

    def _fetch_migrated_states():
        with session_scope(hass=hass) as session:
            states = session.query(States).all()
            assert len(states) == 3
            return {state.state_id: _object_as_dict(state) for state in states}

    # Run again with new schema, let migration run
    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass) as instance,
    ):
        instance.recorder_and_worker_thread_ids.add(threading.get_ident())

        await hass.async_block_till_done()
        await async_wait_recording_done(hass)
        await async_wait_recording_done(hass)

        states_by_metadata_id = await instance.async_add_executor_job(
            _fetch_migrated_states
        )

        await hass.async_stop()
        await hass.async_block_till_done()

    assert len(states_by_metadata_id) == 3
    for state in states_by_metadata_id.values():
        assert state["last_updated_ts"] is not None

    by_entity_id = {
        state["entity_id"]: state for state in states_by_metadata_id.values()
    }
    assert by_entity_id["state.test_state1"]["last_updated_ts"] == 1477685632.452529
    assert by_entity_id["state.test_state2"]["last_updated_ts"] == 1477685632.552529
    assert (
        by_entity_id["state.already_migrated"]["last_updated_ts"] == 1477685632.452529
    )