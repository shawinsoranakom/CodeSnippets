async def test_receive_backup_busy_manager(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    create_backup: AsyncMock,
) -> None:
    """Test receive backup with a busy manager."""
    new_backup = NewBackup(backup_job_id="time-123")
    backup_task: asyncio.Future[WrittenBackup] = asyncio.Future()
    create_backup.return_value = (new_backup, backup_task)
    await setup_backup_integration(hass)
    client = await hass_client()
    ws_client = await hass_ws_client(hass)

    upload_data = "test"

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})
    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": "idle"}

    result = await ws_client.receive_json()
    assert result["success"] is True

    await ws_client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["backup.local"]}
    )
    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }
    result = await ws_client.receive_json()
    assert result["success"] is True
    assert result["result"] == {"backup_job_id": "time-123"}

    assert create_backup.call_count == 1

    resp = await client.post(
        "/api/backup/upload?agent_id=backup.local",
        data={"file": StringIO(upload_data)},
    )

    assert resp.status == 500
    assert (
        await resp.text()
        == "Can't upload backup file: Backup manager busy: create_backup"
    )

    # finish the backup
    backup_task.set_result(
        WrittenBackup(
            addon_errors={},
            backup=TEST_BACKUP_ABC123,
            folder_errors={},
            open_stream=AsyncMock(),
            release_stream=AsyncMock(),
        )
    )
    await hass.async_block_till_done()