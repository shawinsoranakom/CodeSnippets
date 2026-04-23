async def test_agents_upload(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
    setup_dsm_with_filestation: MagicMock,
) -> None:
    """Test agent upload backup."""
    client = await hass_client()
    backup_id = "test-backup"
    test_backup = AgentBackup(
        addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
        backup_id=backup_id,
        database_included=True,
        date="1970-01-01T00:00:00.000Z",
        extra_metadata={},
        folders=[Folder.MEDIA, Folder.SHARE],
        homeassistant_included=True,
        homeassistant_version="2024.12.0",
        name="Test",
        protected=True,
        size=0,
    )
    base_filename = "Test_1970-01-01_00.00_00000000"

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
        fetch_backup.return_value = test_backup
        resp = await client.post(
            "/api/backup/upload?agent_id=synology_dsm.mocked_syno_dsm_entry",
            data={"file": StringIO("test")},
        )

    assert resp.status == 201
    assert f"Uploading backup {backup_id}" in caplog.text
    mock: AsyncMock = setup_dsm_with_filestation.file.upload_file
    assert len(mock.mock_calls) == 2
    assert mock.call_args_list[0].kwargs["filename"] == f"{base_filename}.tar"
    assert mock.call_args_list[0].kwargs["path"] == "/ha_backup/my_backup_path"
    assert mock.call_args_list[1].kwargs["filename"] == f"{base_filename}_meta.json"
    assert mock.call_args_list[1].kwargs["path"] == "/ha_backup/my_backup_path"