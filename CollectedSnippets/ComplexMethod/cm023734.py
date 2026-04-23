async def test_migrate_states_context_ids(
    async_test_recorder: RecorderInstanceContextManager,
    indices_to_drop: list[tuple[str, str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we can migrate old uuid context ids and ulid context ids to binary format."""
    importlib.import_module(SCHEMA_MODULE_32)
    old_db_schema = sys.modules[SCHEMA_MODULE_32]

    test_uuid = uuid.uuid4()
    uuid_hex = test_uuid.hex
    uuid_bin = test_uuid.bytes

    def _insert_states():
        with session_scope(hass=hass) as session:
            session.add_all(
                (
                    old_db_schema.States(
                        entity_id="state.old_uuid_context_id",
                        last_updated_ts=1477721632.452529,
                        context_id=uuid_hex,
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.States(
                        entity_id="state.empty_context_id",
                        last_updated_ts=1477721632.552529,
                        context_id=None,
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.States(
                        entity_id="state.ulid_context_id",
                        last_updated_ts=1477721632.552529,
                        context_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                        context_id_bin=None,
                        context_user_id="9400facee45711eaa9308bfd3d19e474",
                        context_user_id_bin=None,
                        context_parent_id="01ARZ3NDEKTSV4RRFFQ69G5FA2",
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.States(
                        entity_id="state.invalid_context_id",
                        last_updated_ts=1477721632.552529,
                        context_id="invalid",
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.States(
                        entity_id="state.garbage_context_id",
                        last_updated_ts=1477721632.552529,
                        context_id="adapt_lgt:b'5Cf*':interval:b'0R'",
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.States(
                        entity_id="state.human_readable_uuid_context_id",
                        last_updated_ts=1477721632.552529,
                        context_id="0ae29799-ee4e-4f45-8116-f582d7d3ee65",
                        context_id_bin=None,
                        context_user_id="0ae29799-ee4e-4f45-8116-f582d7d3ee65",
                        context_user_id_bin=None,
                        context_parent_id="0ae29799-ee4e-4f45-8116-f582d7d3ee65",
                        context_parent_id_bin=None,
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
        patch.object(migration.StatesContextIDMigration, "migrate_data"),
        patch(CREATE_ENGINE_TARGET, new=_create_engine_test),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await instance.async_add_executor_job(_insert_states)

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

    def _object_as_dict(obj):
        return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

    def _fetch_migrated_states():
        with session_scope(hass=hass) as session:
            events = (
                session.query(States)
                .filter(
                    States.entity_id.in_(
                        [
                            "state.old_uuid_context_id",
                            "state.empty_context_id",
                            "state.ulid_context_id",
                            "state.invalid_context_id",
                            "state.garbage_context_id",
                            "state.human_readable_uuid_context_id",
                        ]
                    )
                )
                .all()
            )
            assert len(events) == 6
            return {state.entity_id: _object_as_dict(state) for state in events}

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
                # Check the context ID migrator is considered non-live
                assert recorder.util.async_migration_is_live(hass) is False
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

                states_by_entity_id = await instance.async_add_executor_job(
                    _fetch_migrated_states
                )

                migration_changes = await instance.async_add_executor_job(
                    _get_migration_id, hass
                )

                # Check the index which will be removed by the migrator no longer exists
                with session_scope(hass=hass) as session:
                    assert (
                        get_index_by_name(session, "states", "ix_states_context_id")
                        is None
                    )

                await hass.async_stop()
                await hass.async_block_till_done()

    # Check the index we removed was recreated
    index_names = [call[1][0].name for call in wrapped_idx_create.mock_calls]
    assert index_names == [index for _, index in indices_to_drop]

    old_uuid_context_id = states_by_entity_id["state.old_uuid_context_id"]
    assert old_uuid_context_id["context_id"] is None
    assert old_uuid_context_id["context_user_id"] is None
    assert old_uuid_context_id["context_parent_id"] is None
    assert old_uuid_context_id["context_id_bin"] == uuid_bin
    assert old_uuid_context_id["context_user_id_bin"] is None
    assert old_uuid_context_id["context_parent_id_bin"] is None

    empty_context_id = states_by_entity_id["state.empty_context_id"]
    assert empty_context_id["context_id"] is None
    assert empty_context_id["context_user_id"] is None
    assert empty_context_id["context_parent_id"] is None
    assert empty_context_id["context_id_bin"].startswith(
        b"\x01X\x0f\x12\xaf("
    )  # 6 bytes of timestamp + random
    assert empty_context_id["context_user_id_bin"] is None
    assert empty_context_id["context_parent_id_bin"] is None

    ulid_context_id = states_by_entity_id["state.ulid_context_id"]
    assert ulid_context_id["context_id"] is None
    assert ulid_context_id["context_user_id"] is None
    assert ulid_context_id["context_parent_id"] is None
    assert (
        bytes_to_ulid(ulid_context_id["context_id_bin"]) == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    )
    assert (
        ulid_context_id["context_user_id_bin"]
        == b"\x94\x00\xfa\xce\xe4W\x11\xea\xa90\x8b\xfd=\x19\xe4t"
    )
    assert (
        bytes_to_ulid(ulid_context_id["context_parent_id_bin"])
        == "01ARZ3NDEKTSV4RRFFQ69G5FA2"
    )

    invalid_context_id = states_by_entity_id["state.invalid_context_id"]
    assert invalid_context_id["context_id"] is None
    assert invalid_context_id["context_user_id"] is None
    assert invalid_context_id["context_parent_id"] is None
    assert invalid_context_id["context_id_bin"].startswith(
        b"\x01X\x0f\x12\xaf("
    )  # 6 bytes of timestamp + random
    assert invalid_context_id["context_user_id_bin"] is None
    assert invalid_context_id["context_parent_id_bin"] is None

    garbage_context_id = states_by_entity_id["state.garbage_context_id"]
    assert garbage_context_id["context_id"] is None
    assert garbage_context_id["context_user_id"] is None
    assert garbage_context_id["context_parent_id"] is None
    assert garbage_context_id["context_id_bin"].startswith(
        b"\x01X\x0f\x12\xaf("
    )  # 6 bytes of timestamp + random
    assert garbage_context_id["context_user_id_bin"] is None
    assert garbage_context_id["context_parent_id_bin"] is None

    human_readable_uuid_context_id = states_by_entity_id[
        "state.human_readable_uuid_context_id"
    ]
    assert human_readable_uuid_context_id["context_id"] is None
    assert human_readable_uuid_context_id["context_user_id"] is None
    assert human_readable_uuid_context_id["context_parent_id"] is None
    assert (
        human_readable_uuid_context_id["context_id_bin"]
        == b"\n\xe2\x97\x99\xeeNOE\x81\x16\xf5\x82\xd7\xd3\xeee"
    )
    assert (
        human_readable_uuid_context_id["context_user_id_bin"]
        == b"\n\xe2\x97\x99\xeeNOE\x81\x16\xf5\x82\xd7\xd3\xeee"
    )
    assert (
        human_readable_uuid_context_id["context_parent_id_bin"]
        == b"\n\xe2\x97\x99\xeeNOE\x81\x16\xf5\x82\xd7\xd3\xeee"
    )

    assert (
        migration_changes[migration.StatesContextIDMigration.migration_id]
        == migration.StatesContextIDMigration.migration_version
    )