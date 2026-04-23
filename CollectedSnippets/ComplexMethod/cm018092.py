async def async_test_recorder(
    recorder_db_url: str,
    enable_nightly_purge: bool,
    enable_statistics: bool,
    enable_missing_statistics: bool,
    enable_schema_validation: bool,
    enable_migrate_event_context_ids: bool,
    enable_migrate_state_context_ids: bool,
    enable_migrate_event_type_ids: bool,
    enable_migrate_entity_ids: bool,
    enable_migrate_event_ids: bool,
) -> AsyncGenerator[RecorderInstanceContextManager]:
    """Yield context manager to setup recorder instance."""
    from homeassistant.components import recorder  # noqa: PLC0415
    from homeassistant.components.recorder import migration  # noqa: PLC0415

    from .components.recorder.common import (  # noqa: PLC0415
        async_recorder_block_till_done,
    )
    from .patch_recorder import real_session_scope  # noqa: PLC0415

    if TYPE_CHECKING:
        from sqlalchemy.orm.session import Session  # noqa: PLC0415

    @contextmanager
    def debug_session_scope(
        *,
        hass: HomeAssistant | None = None,
        session: Session | None = None,
        exception_filter: Callable[[Exception], bool] | None = None,
        read_only: bool = False,
    ) -> Generator[Session]:
        """Wrap session_scope to bark if we create nested sessions."""
        if thread_session.has_session:
            raise RuntimeError(
                f"Thread '{threading.current_thread().name}' already has an "
                "active session"
            )
        thread_session.has_session = True
        try:
            with real_session_scope(
                hass=hass,
                session=session,
                exception_filter=exception_filter,
                read_only=read_only,
            ) as ses:
                yield ses
        finally:
            thread_session.has_session = False

    nightly = recorder.Recorder.async_nightly_tasks if enable_nightly_purge else None
    stats = recorder.Recorder.async_periodic_statistics if enable_statistics else None
    schema_validate = (
        migration._find_schema_errors
        if enable_schema_validation
        else itertools.repeat(set())
    )
    compile_missing = (
        recorder.Recorder._schedule_compile_missing_statistics
        if enable_missing_statistics
        else None
    )
    migrate_states_context_ids = (
        migration.StatesContextIDMigration.migrate_data
        if enable_migrate_state_context_ids
        else None
    )
    migrate_events_context_ids = (
        migration.EventsContextIDMigration.migrate_data
        if enable_migrate_event_context_ids
        else None
    )
    migrate_event_type_ids = (
        migration.EventTypeIDMigration.migrate_data
        if enable_migrate_event_type_ids
        else None
    )
    migrate_entity_ids = (
        migration.EntityIDMigration.migrate_data if enable_migrate_entity_ids else None
    )
    post_migrate_event_ids = (
        migration.EventIDPostMigration.needs_migrate_impl
        if enable_migrate_event_ids
        else lambda _1, _2, _3: migration.DataMigrationStatus(
            needs_migrate=False, migration_done=True
        )
    )
    with (
        patch(
            "homeassistant.components.recorder.Recorder.async_nightly_tasks",
            side_effect=nightly,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.Recorder.async_periodic_statistics",
            side_effect=stats,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration._find_schema_errors",
            side_effect=schema_validate,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration.EventsContextIDMigration.migrate_data",
            side_effect=migrate_events_context_ids,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration.StatesContextIDMigration.migrate_data",
            side_effect=migrate_states_context_ids,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration.EventTypeIDMigration.migrate_data",
            side_effect=migrate_event_type_ids,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration.EntityIDMigration.migrate_data",
            side_effect=migrate_entity_ids,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.migration.EventIDPostMigration.needs_migrate_impl",
            side_effect=post_migrate_event_ids,
            autospec=True,
        ),
        patch(
            "homeassistant.components.recorder.Recorder._schedule_compile_missing_statistics",
            side_effect=compile_missing,
            autospec=True,
        ),
        patch.object(
            patch_recorder,
            "real_session_scope",
            side_effect=debug_session_scope,
            autospec=True,
        ),
    ):

        @asynccontextmanager
        async def async_test_recorder(
            hass: HomeAssistant,
            config: ConfigType | None = None,
            *,
            expected_setup_result: bool = True,
            wait_recorder: bool = True,
            wait_recorder_setup: bool = True,
        ) -> AsyncGenerator[recorder.Recorder]:
            """Setup and return recorder instance."""
            await _async_init_recorder_component(
                hass,
                config,
                recorder_db_url,
                expected_setup_result=expected_setup_result,
                wait_setup=wait_recorder_setup,
            )
            await hass.async_block_till_done()
            instance = hass.data[recorder.DATA_INSTANCE]
            # The recorder's worker is not started until Home Assistant is running
            if hass.state is CoreState.running and wait_recorder:
                await async_recorder_block_till_done(hass)
            try:
                yield instance
            finally:
                if instance.is_alive():
                    await instance._async_shutdown(None)

        yield async_test_recorder