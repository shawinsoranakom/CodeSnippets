async def test_agents_upload(
    hass_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    agent_backup: AgentBackup,
) -> None:
    """Test agent upload backup."""
    client = await hass_client()
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=agent_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=agent_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        # we must emit at least two chunks
        # the "appendix" chunk triggers the upload of the final buffer part
        mocked_open.return_value.read = Mock(
            side_effect=[
                b"a" * agent_backup.size,
                b"appendix",
                b"",
            ]
        )
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

        assert resp.status == 201
        assert f"Uploading backup {agent_backup.backup_id}" in caplog.text
        if agent_backup.size < MULTIPART_MIN_PART_SIZE_BYTES:
            # single part + metadata both as regular upload (no multiparts)
            assert mock_client.create_multipart_upload.await_count == 0
            assert mock_client.put_object.await_count == 2
        else:
            assert "Uploading final part" in caplog.text
            # 2 parts as multipart + metadata as regular upload
            assert mock_client.create_multipart_upload.await_count == 1
            assert mock_client.upload_part.await_count == 2
            assert mock_client.complete_multipart_upload.await_count == 1
            assert mock_client.put_object.await_count == 1