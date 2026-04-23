async def test_database_lock_and_overflow_checks_available_memory(
    hass: HomeAssistant,
    async_setup_recorder_instance: RecorderInstanceGenerator,
    caplog: pytest.LogCaptureFixture,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test writing events during lock leading to overflow the queue causes the database to unlock.

    This test is specific for SQLite: Locking is not implemented for other engines.

    Use file DB, in memory DB cannot do write locks.
    """
    config = {
        recorder.CONF_COMMIT_INTERVAL: 0,
    }

    def _get_db_events():
        with session_scope(hass=hass, read_only=True) as session:
            return list(
                session.query(Events).filter(
                    Events.event_type_id.in_(select_event_type_ids(event_types))
                )
            )

    with patch(
        "homeassistant.components.recorder.core.QUEUE_CHECK_INTERVAL",
        timedelta(seconds=1),
    ):
        await async_setup_recorder_instance(hass, config)
        await hass.async_block_till_done()
    event_type = "EVENT_TEST"
    event_types = (event_type,)
    await async_wait_recording_done(hass)
    min_available_memory = 256 * 1024**2

    out_of_ram = False

    def _get_available_memory(*args: Any, **kwargs: Any) -> int:
        nonlocal out_of_ram
        return min_available_memory / 2 if out_of_ram else min_available_memory

    with (
        patch.object(recorder.core, "MAX_QUEUE_BACKLOG_MIN_VALUE", 1),
        patch.object(
            recorder.core,
            "MIN_AVAILABLE_MEMORY_FOR_QUEUE_BACKLOG",
            min_available_memory,
        ),
        patch.object(recorder.core, "DB_LOCK_QUEUE_CHECK_TIMEOUT", 0.01),
        patch.object(
            recorder.core.Recorder,
            "_available_memory",
            side_effect=_get_available_memory,
        ),
    ):
        instance = get_instance(hass)

        assert await instance.lock_database()

        db_events = await instance.async_add_executor_job(_get_db_events)
        assert len(db_events) == 0
        # Record up to the extended limit (which takes into account the available memory)
        for _ in range(2):
            event_data = {"test_attr": 5, "test_attr_10": "nice"}
            hass.bus.async_fire(event_type, event_data)

        def _wait_database_unlocked():
            return instance._database_lock_task.database_unlock.wait(0.2)

        databack_unlocked = await hass.async_add_executor_job(_wait_database_unlocked)
        assert not databack_unlocked

        db_events = await instance.async_add_executor_job(_get_db_events)
        assert len(db_events) == 0

        assert "Database queue backlog reached more than" not in caplog.text

        out_of_ram = True
        # Record beyond the extended limit (which takes into account the available memory)
        for _ in range(20):
            event_data = {"test_attr": 5, "test_attr_10": "nice"}
            hass.bus.async_fire(event_type, event_data)

        # Check that this causes the queue to overflow and write succeeds
        # even before unlocking.
        await async_wait_recording_done(hass)

        assert not instance.unlock_database()

        assert "Database queue backlog reached more than" in caplog.text

        db_events = await instance.async_add_executor_job(_get_db_events)
        assert len(db_events) >= 2

    issue = issue_registry.async_get_issue(DOMAIN, "backup_failed_out_of_resources")
    assert issue is not None
    assert "start_time" in issue.translation_placeholders
    start_time = issue.translation_placeholders["start_time"]
    assert start_time is not None
    # Should be in H:M:S format
    assert start_time.count(":") == 2