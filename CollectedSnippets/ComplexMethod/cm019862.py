async def test_upload_progress_debounced(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
) -> None:
    """Test that rapid upload progress events are debounced.

    Verify that when the on_progress callback is called multiple times during
    the debounce cooldown period, only the latest event is fired.
    """
    agent_ids = ["test.remote"]
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.remote"])
    manager = hass.data[DATA_MANAGER]

    remote_agent = mock_agents["test.remote"]

    progress_done = asyncio.Event()
    upload_done = asyncio.Event()

    async def upload_with_progress(**kwargs: Any) -> None:
        """Upload and report progress."""
        on_progress = kwargs["on_progress"]
        # First call fires immediately
        on_progress(bytes_uploaded=100)
        # These two are buffered during cooldown; 1000 should replace 500
        on_progress(bytes_uploaded=500)
        on_progress(bytes_uploaded=1000)
        progress_done.set()
        await upload_done.wait()

    remote_agent.async_upload_backup.side_effect = upload_with_progress

    # Subscribe directly to collect all events
    events: list[Any] = []
    manager.async_subscribe_events(events.append)

    ws_client = await hass_ws_client(hass)

    with patch("pathlib.Path.open", mock_open(read_data=b"test")):
        await ws_client.send_json_auto_id(
            {"type": "backup/generate", "agent_ids": agent_ids}
        )
        result = await ws_client.receive_json()
        assert result["success"] is True

        # Wait for upload to reach the sync point (progress reported, upload paused)
        await progress_done.wait()

        # At this point the debouncer's cooldown timer is pending.
        # The first event (100 bytes) fired immediately, 500 and 1000 are buffered.
        remote_events = [
            e
            for e in events
            if isinstance(e, UploadBackupEvent) and e.agent_id == "test.remote"
        ]
        assert len(remote_events) == 1
        assert remote_events[0].uploaded_bytes == 100

        # Advance time past the cooldown to trigger the debouncer timer.
        # This fires the coalesced event: 500 was replaced by 1000.
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))

        remote_events = [
            e
            for e in events
            if isinstance(e, UploadBackupEvent) and e.agent_id == "test.remote"
        ]
        assert len(remote_events) == 2
        assert remote_events[0].uploaded_bytes == 100
        assert remote_events[1].uploaded_bytes == 1000

        # Let the upload finish
        upload_done.set()
        # Fire pending timers so the backup task can complete
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=10), fire_all=True
        )
        await hass.async_block_till_done()

    # Check the final 100% progress event is sent, that is sent for every agent
    remote_events = [
        e
        for e in events
        if isinstance(e, UploadBackupEvent) and e.agent_id == "test.remote"
    ]
    assert len(remote_events) == 3
    assert remote_events[2].uploaded_bytes == remote_events[2].total_bytes