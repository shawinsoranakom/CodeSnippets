async def test_agents_upload_on_progress(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    test_backup: AgentBackup,
) -> None:
    """Test agent upload backup emits UploadBackupEvent via on_progress."""
    client = await hass_client()

    manager = hass.data[DATA_MANAGER]
    events: list[UploadBackupEvent] = []

    def _collect(event: UploadBackupEvent) -> None:
        if isinstance(event, UploadBackupEvent):
            events.append(event)

    unsub = manager.async_subscribe_events(_collect)

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=test_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(
            side_effect=[
                b"a" * test_backup.size,
                b"",
            ]
        )
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

    unsub()

    assert resp.status == 201
    agent_id = f"{DOMAIN}.{mock_config_entry.entry_id}"
    agent_events = [e for e in events if e.agent_id == agent_id]
    assert len(agent_events) >= 2
    assert all(e.total_bytes == test_backup.size for e in agent_events)
    # Verify events report distinct increasing byte counts
    uploaded_bytes = [e.uploaded_bytes for e in agent_events]
    assert uploaded_bytes == sorted(uploaded_bytes)
    assert len(set(uploaded_bytes)) == len(uploaded_bytes)
    # Verify at least one intermediate event (uploaded_bytes < total_bytes)
    assert agent_events[0].uploaded_bytes < agent_events[0].total_bytes