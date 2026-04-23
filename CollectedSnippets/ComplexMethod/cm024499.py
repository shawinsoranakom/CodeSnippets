async def test_agents_upload_emits_progress_events(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_client: ClientSessionGenerator,
    webdav_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test upload emits progress events with bytes from upload_iter callbacks."""
    test_backup = AgentBackup.from_dict(BACKUP_METADATA)
    client = await hass_client()
    ws_client = await hass_ws_client(hass)
    observed_progress_bytes: list[int] = []

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await ws_client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await ws_client.receive_json()
    assert response["success"] is True

    async def _mock_upload_iter(*args: object, **kwargs: object) -> None:
        """Mock upload and trigger progress callback for backup upload."""
        path = args[1]
        if path.endswith(".tar"):
            progress = kwargs.get("progress")
            assert callable(progress)
            progress(1024, test_backup.size)
            progress(test_backup.size, test_backup.size)

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
        ) as fetch_backup,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        webdav_client.upload_iter.side_effect = _mock_upload_iter
        fetch_backup.return_value = test_backup
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )
        await hass.async_block_till_done()

    assert resp.status == 201

    # Gather progress events from the upload flow.
    reached_idle = False
    for _ in range(20):
        response = await ws_client.receive_json()
        event = response.get("event")

        if event is None:
            continue

        if (
            event.get("manager_state") == "receive_backup"
            and event.get("agent_id") == f"{DOMAIN}.{mock_config_entry.entry_id}"
            and "uploaded_bytes" in event
        ):
            observed_progress_bytes.append(event["uploaded_bytes"])

        if event == {"manager_state": "idle"}:
            reached_idle = True
            break

    assert reached_idle
    assert 1024 in observed_progress_bytes
    assert test_backup.size in observed_progress_bytes