async def test_reader_writer_create_missing_reference_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    supervisor_event: dict[str, Any],
) -> None:
    """Test missing reference error when generating a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["hassio.local"], "name": "Test"}
    )
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"backup_job_id": TEST_JOB_ID}

    assert supervisor_client.backups.partial_backup.call_count == 1

    await client.send_json_auto_id(
        {"type": "supervisor/event", "data": supervisor_event}
    )
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": "upload_failed",
        "stage": None,
        "state": "failed",
    }

    await hass.async_block_till_done()

    assert supervisor_client.backups.backup_info.call_count == 0
    assert supervisor_client.backups.download_backup.call_count == 0
    assert supervisor_client.backups.remove_backup.call_count == 0

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}