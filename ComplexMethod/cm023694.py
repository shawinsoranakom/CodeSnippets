async def test_schema_migrate(
    hass: HomeAssistant,
    recorder_db_url: str,
    async_setup_recorder_instance: RecorderInstanceGenerator,
    instrument_migration: InstrumentedMigration,
    start_version,
    live,
) -> None:
    """Test the full schema migration logic.

    We're just testing that the logic can execute successfully here without
    throwing exceptions. Maintaining a set of assertions based on schema
    inspection could quickly become quite cumbersome.
    """

    real_create_index = recorder.migration._create_index
    create_calls = 0

    def _create_engine_test(*args, **kwargs):
        """Test version of create_engine that initializes with old schema.

        This simulates an existing db with the old schema.
        """
        module = f"tests.components.recorder.db_schema_{start_version!s}"
        importlib.import_module(module)
        old_models = sys.modules[module]
        engine = create_engine(*args, **kwargs)
        old_models.Base.metadata.create_all(engine)
        if start_version > 0:
            with Session(engine) as session:
                session.add(
                    recorder.db_schema.SchemaChanges(schema_version=start_version)
                )
                session.commit()
        return engine

    def _mock_setup_run(self):
        self.run_info = RecorderRuns(
            start=self.recorder_runs_manager.recording_start, created=dt_util.utcnow()
        )

    def _sometimes_failing_create_index(*args, **kwargs):
        """Make the first index create raise a retryable error to ensure we retry."""
        if recorder_db_url.startswith("mysql://"):
            nonlocal create_calls
            if create_calls < 1:
                create_calls += 1
                mysql_exception = OperationalError("statement", {}, [])
                mysql_exception.orig = Exception(1205, "retryable")
                raise mysql_exception
        real_create_index(*args, **kwargs)

    with (
        patch(
            "homeassistant.components.recorder.core.create_engine",
            new=_create_engine_test,
        ),
        patch(
            "homeassistant.components.recorder.Recorder._setup_run",
            side_effect=_mock_setup_run,
            autospec=True,
        ) as setup_run,
        patch("homeassistant.components.recorder.util.time.sleep"),
        patch(
            "homeassistant.components.recorder.migration._create_index",
            wraps=_sometimes_failing_create_index,
        ),
        patch(
            "homeassistant.components.recorder.Recorder._process_state_changed_event_into_session",
        ),
        patch(
            "homeassistant.components.recorder.Recorder._process_non_state_changed_event_into_session",
        ),
        patch(
            "homeassistant.components.recorder.Recorder._pre_process_startup_events",
        ),
    ):
        await async_setup_recorder_instance(
            hass, wait_recorder=False, wait_recorder_setup=live
        )
        await hass.async_add_executor_job(instrument_migration.migration_started.wait)
        assert recorder.util.async_migration_in_progress(hass) is True
        await async_wait_recorder(hass)

        assert recorder.util.async_migration_in_progress(hass) is True
        assert recorder.util.async_migration_is_live(hass) == live
        instrument_migration.migration_stall.set()
        await hass.async_block_till_done()
        await hass.async_add_executor_job(instrument_migration.live_migration_done.wait)
        await async_wait_recording_done(hass)
        assert instrument_migration.migration_version == db_schema.SCHEMA_VERSION
        assert setup_run.called
        assert recorder.util.async_migration_in_progress(hass) is not True
        assert instrument_migration.apply_update_mock.called