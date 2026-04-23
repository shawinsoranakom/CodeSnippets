async def test_database_lock_and_overflow(
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

    with (
        patch.object(recorder.core, "MAX_QUEUE_BACKLOG_MIN_VALUE", 1),
        patch.object(recorder.core, "DB_LOCK_QUEUE_CHECK_TIMEOUT", 0.01),
        patch.object(
            recorder.core, "MIN_AVAILABLE_MEMORY_FOR_QUEUE_BACKLOG", sys.maxsize
        ),
    ):
        await async_setup_recorder_instance(hass, config)
        await hass.async_block_till_done()
        event_type = "EVENT_TEST"
        event_types = (event_type,)

        instance = get_instance(hass)

        await instance.lock_database()

        event_data = {"test_attr": 5, "test_attr_10": "nice"}
        hass.bus.async_fire(event_type, event_data)

        # Check that this causes the queue to overflow and write succeeds
        # even before unlocking.
        await async_wait_recording_done(hass)

        db_events = await instance.async_add_executor_job(_get_db_events)
        assert len(db_events) == 1

        assert "Database queue backlog reached more than" in caplog.text
        assert not instance.unlock_database()

    issue = issue_registry.async_get_issue(DOMAIN, "backup_failed_out_of_resources")
    assert issue is not None
    assert "start_time" in issue.translation_placeholders
    start_time = issue.translation_placeholders["start_time"]
    assert start_time is not None
    # Should be in H:M:S format
    assert start_time.count(":") == 2