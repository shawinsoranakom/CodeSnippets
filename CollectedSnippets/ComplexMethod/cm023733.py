async def test_migrate_events_context_ids(
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

    def _insert_events():
        with session_scope(hass=hass) as session:
            session.add_all(
                (
                    old_db_schema.Events(
                        event_type="old_uuid_context_id_event",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=1877721632.452529,
                        context_id=uuid_hex,
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.Events(
                        event_type="empty_context_id_event",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=1877721632.552529,
                        context_id=None,
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.Events(
                        event_type="ulid_context_id_event",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=1877721632.552529,
                        context_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                        context_id_bin=None,
                        context_user_id="9400facee45711eaa9308bfd3d19e474",
                        context_user_id_bin=None,
                        context_parent_id="01ARZ3NDEKTSV4RRFFQ69G5FA2",
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.Events(
                        event_type="invalid_context_id_event",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=1877721632.552529,
                        context_id="invalid",
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.Events(
                        event_type="garbage_context_id_event",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=1277721632.552529,
                        context_id="adapt_lgt:b'5Cf*':interval:b'0R'",
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
                        context_parent_id_bin=None,
                    ),
                    old_db_schema.Events(
                        event_type="event_with_garbage_context_id_no_time_fired_ts",
                        event_data=None,
                        origin_idx=0,
                        time_fired=None,
                        time_fired_ts=None,
                        context_id="adapt_lgt:b'5Cf*':interval:b'0R'",
                        context_id_bin=None,
                        context_user_id=None,
                        context_user_id_bin=None,
                        context_parent_id=None,
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
        patch.object(migration.EventsContextIDMigration, "migrate_data"),
        patch(CREATE_ENGINE_TARGET, new=_create_engine_test),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await instance.async_add_executor_job(_insert_events)

            await async_wait_recording_done(hass)
            now = dt_util.utcnow()
            expected_ulid_fallback_start = ulid_to_bytes(ulid_at_time(now.timestamp()))[
                0:6
            ]
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

    def _fetch_migrated_events():
        with session_scope(hass=hass) as session:
            events = (
                session.query(Events)
                .filter(
                    Events.event_type.in_(
                        [
                            "old_uuid_context_id_event",
                            "empty_context_id_event",
                            "ulid_context_id_event",
                            "invalid_context_id_event",
                            "garbage_context_id_event",
                            "event_with_garbage_context_id_no_time_fired_ts",
                        ]
                    )
                )
                .all()
            )
            assert len(events) == 6
            return {event.event_type: _object_as_dict(event) for event in events}

    # Run again with new schema, let migration run
    async with async_test_home_assistant() as hass:
        with (
            freeze_time(now),
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

                events_by_type = await instance.async_add_executor_job(
                    _fetch_migrated_events
                )

                migration_changes = await instance.async_add_executor_job(
                    _get_migration_id, hass
                )

                # Check the index which will be removed by the migrator no longer exists
                with session_scope(hass=hass) as session:
                    assert (
                        get_index_by_name(session, "events", "ix_events_context_id")
                        is None
                    )

                await hass.async_stop()
                await hass.async_block_till_done()

    # Check the index we removed was recreated
    index_names = [call[1][0].name for call in wrapped_idx_create.mock_calls]
    assert index_names == [index for _, index in indices_to_drop]

    old_uuid_context_id_event = events_by_type["old_uuid_context_id_event"]
    assert old_uuid_context_id_event["context_id"] is None
    assert old_uuid_context_id_event["context_user_id"] is None
    assert old_uuid_context_id_event["context_parent_id"] is None
    assert old_uuid_context_id_event["context_id_bin"] == uuid_bin
    assert old_uuid_context_id_event["context_user_id_bin"] is None
    assert old_uuid_context_id_event["context_parent_id_bin"] is None

    empty_context_id_event = events_by_type["empty_context_id_event"]
    assert empty_context_id_event["context_id"] is None
    assert empty_context_id_event["context_user_id"] is None
    assert empty_context_id_event["context_parent_id"] is None
    assert empty_context_id_event["context_id_bin"].startswith(
        b"\x01\xb50\xeeO("
    )  # 6 bytes of timestamp + random
    assert empty_context_id_event["context_user_id_bin"] is None
    assert empty_context_id_event["context_parent_id_bin"] is None

    ulid_context_id_event = events_by_type["ulid_context_id_event"]
    assert ulid_context_id_event["context_id"] is None
    assert ulid_context_id_event["context_user_id"] is None
    assert ulid_context_id_event["context_parent_id"] is None
    assert (
        bytes_to_ulid(ulid_context_id_event["context_id_bin"])
        == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    )
    assert (
        ulid_context_id_event["context_user_id_bin"]
        == b"\x94\x00\xfa\xce\xe4W\x11\xea\xa90\x8b\xfd=\x19\xe4t"
    )
    assert (
        bytes_to_ulid(ulid_context_id_event["context_parent_id_bin"])
        == "01ARZ3NDEKTSV4RRFFQ69G5FA2"
    )

    invalid_context_id_event = events_by_type["invalid_context_id_event"]
    assert invalid_context_id_event["context_id"] is None
    assert invalid_context_id_event["context_user_id"] is None
    assert invalid_context_id_event["context_parent_id"] is None
    assert invalid_context_id_event["context_id_bin"].startswith(
        b"\x01\xb50\xeeO("
    )  # 6 bytes of timestamp + random
    assert invalid_context_id_event["context_user_id_bin"] is None
    assert invalid_context_id_event["context_parent_id_bin"] is None

    garbage_context_id_event = events_by_type["garbage_context_id_event"]
    assert garbage_context_id_event["context_id"] is None
    assert garbage_context_id_event["context_user_id"] is None
    assert garbage_context_id_event["context_parent_id"] is None
    assert garbage_context_id_event["context_id_bin"].startswith(
        b"\x01)~$\xdf("
    )  # 6 bytes of timestamp + random
    assert garbage_context_id_event["context_user_id_bin"] is None
    assert garbage_context_id_event["context_parent_id_bin"] is None

    event_with_garbage_context_id_no_time_fired_ts = events_by_type[
        "event_with_garbage_context_id_no_time_fired_ts"
    ]
    assert event_with_garbage_context_id_no_time_fired_ts["context_id"] is None
    assert event_with_garbage_context_id_no_time_fired_ts["context_user_id"] is None
    assert event_with_garbage_context_id_no_time_fired_ts["context_parent_id"] is None
    assert event_with_garbage_context_id_no_time_fired_ts["context_id_bin"].startswith(
        expected_ulid_fallback_start
    )  # 6 bytes of timestamp + random
    assert event_with_garbage_context_id_no_time_fired_ts["context_user_id_bin"] is None
    assert (
        event_with_garbage_context_id_no_time_fired_ts["context_parent_id_bin"] is None
    )

    assert (
        migration_changes[migration.EventsContextIDMigration.migration_id]
        == migration.EventsContextIDMigration.migration_version
    )