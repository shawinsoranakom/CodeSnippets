async def test_service_disable_run_information_recorded(
    async_test_recorder: RecorderInstanceContextManager,
) -> None:
    """Test that runs are still recorded when recorder is disabled."""

    def get_recorder_runs(hass: HomeAssistant) -> list:
        with session_scope(hass=hass, read_only=True) as session:
            return list(session.query(RecorderRuns))

    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass) as instance,
    ):
        await hass.async_start()
        await async_wait_recording_done(hass)

        db_run_info = await instance.async_add_executor_job(get_recorder_runs, hass)
        assert len(db_run_info) == 1
        assert db_run_info[0].start is not None
        assert db_run_info[0].end is None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISABLE,
            {},
            blocking=True,
        )

        await async_wait_recording_done(hass)
        await hass.async_stop()

    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass) as instance,
    ):
        await hass.async_start()
        await async_wait_recording_done(hass)

        db_run_info = await instance.async_add_executor_job(get_recorder_runs, hass)
        assert len(db_run_info) == 2
        assert db_run_info[0].start is not None
        assert db_run_info[0].end is not None
        assert db_run_info[1].start is not None
        assert db_run_info[1].end is None

        await hass.async_stop()