async def test_recorder_info_migration_queue_exhausted(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    async_test_recorder: RecorderInstanceContextManager,
    instrument_migration: InstrumentedMigration,
) -> None:
    """Test getting recorder status when recorder queue is exhausted."""
    assert recorder.util.async_migration_in_progress(hass) is False

    with (
        patch(
            "homeassistant.components.recorder.core.create_engine",
            new=create_engine_test,
        ),
        patch.object(recorder.core, "MAX_QUEUE_BACKLOG_MIN_VALUE", 1),
        patch.object(
            recorder.core, "MIN_AVAILABLE_MEMORY_FOR_QUEUE_BACKLOG", sys.maxsize
        ),
    ):
        async with async_test_recorder(
            hass, wait_recorder=False, wait_recorder_setup=False
        ):
            await hass.async_add_executor_job(
                instrument_migration.migration_started.wait
            )
            assert recorder.util.async_migration_in_progress(hass) is True
            await async_wait_recorder(hass)
            hass.states.async_set("my.entity", "on", {})
            await hass.async_block_till_done()

            # Detect queue full
            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=2))
            await hass.async_block_till_done()

            client = await hass_ws_client()

            # Check the status
            await client.send_json_auto_id({"type": "recorder/info"})
            response = await client.receive_json()
            assert response["success"]
            assert response["result"]["migration_in_progress"] is True
            assert response["result"]["recording"] is False
            assert response["result"]["thread_running"] is True

            # Let migration finish
            instrument_migration.migration_stall.set()
            await async_wait_recording_done(hass)

            # Check the status after migration finished
            await client.send_json_auto_id({"type": "recorder/info"})
            response = await client.receive_json()
            assert response["success"]
            assert response["result"]["migration_in_progress"] is False
            assert response["result"]["recording"] is True
            assert response["result"]["thread_running"] is True