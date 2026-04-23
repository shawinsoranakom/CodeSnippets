async def test_upload_progress_event(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
) -> None:
    """Test that upload progress events are fired when an agent reports progress."""
    agent_ids = [LOCAL_AGENT_ID, "test.remote"]
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.remote"])

    remote_agent = mock_agents["test.remote"]
    original_side_effect = remote_agent.async_upload_backup.side_effect

    async def upload_with_progress(**kwargs: Any) -> None:
        """Upload and report progress."""
        on_progress = kwargs["on_progress"]
        on_progress(bytes_uploaded=500)
        on_progress(bytes_uploaded=1000)
        await original_side_effect(**kwargs)

    remote_agent.async_upload_backup.side_effect = upload_with_progress

    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    result = await ws_client.receive_json()
    assert result["success"] is True

    with patch("pathlib.Path.open", mock_open(read_data=b"test")):
        await ws_client.send_json_auto_id(
            {"type": "backup/generate", "agent_ids": agent_ids}
        )
        result = await ws_client.receive_json()
        assert result["event"]["manager_state"] == BackupManagerState.CREATE_BACKUP

        result = await ws_client.receive_json()
        assert result["success"] is True

        await hass.async_block_till_done()

    # Consume intermediate stage events (home_assistant, upload_to_agents)
    result = await ws_client.receive_json()
    assert result["event"]["stage"] == CreateBackupStage.HOME_ASSISTANT

    result = await ws_client.receive_json()
    assert result["event"]["stage"] == CreateBackupStage.UPLOAD_TO_AGENTS

    # Collect all upload progress events until the finishing backup stage event
    progress_events = []
    result = await ws_client.receive_json()
    while "uploaded_bytes" in result["event"]:
        progress_events.append(result["event"])
        result = await ws_client.receive_json()

    # Verify progress events from the remote agent (500 from agent + final from manager)
    remote_progress = [e for e in progress_events if e["agent_id"] == "test.remote"]
    assert len(remote_progress) == 2
    assert remote_progress[0]["uploaded_bytes"] == 500
    assert remote_progress[1]["uploaded_bytes"] == remote_progress[1]["total_bytes"]

    # Verify progress event from the local agent (final from manager)
    local_progress = [e for e in progress_events if e["agent_id"] == LOCAL_AGENT_ID]
    assert len(local_progress) == 1
    assert local_progress[0]["uploaded_bytes"] == local_progress[0]["total_bytes"]

    assert result["event"]["stage"] == CreateBackupStage.CLEANING_UP

    result = await ws_client.receive_json()
    assert result["event"]["state"] == CreateBackupState.COMPLETED

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}