async def test_receive_backup(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    agent_id_params: str,
    open_call_count: int,
    move_call_count: int,
    move_path_names: list[str],
    remote_agent_backups: dict[str, AgentBackup],
    remote_agent_backup_data: bytes | None,
    temp_file_unlink_call_count: int,
) -> None:
    """Test receive backup and upload to the local and a remote agent."""
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.remote"])
    # Make sure we wait for Platform.EVENT and Platform.SENSOR to be fully processed,
    # to avoid interference with the Path.open patching below which is used to verify
    # that the file is written to the expected location.
    await hass.async_block_till_done(True)
    client = await hass_client()

    upload_data = "test"
    open_mock = mock_open(read_data=upload_data.encode(encoding="utf-8"))

    with (
        patch("pathlib.Path.open", open_mock),
        patch(
            "homeassistant.components.backup.manager.make_backup_dir"
        ) as make_backup_dir_mock,
        patch("shutil.move") as move_mock,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_BACKUP_ABC123,
        ),
        patch("pathlib.Path.unlink") as unlink_mock,
    ):
        resp = await client.post(
            f"/api/backup/upload?{agent_id_params}",
            data={"file": StringIO(upload_data)},
        )
        await hass.async_block_till_done()

    assert resp.status == 201
    assert open_mock.call_count == open_call_count
    assert make_backup_dir_mock.call_count == move_call_count + 1
    assert move_mock.call_count == move_call_count
    for index, name in enumerate(move_path_names):
        assert move_mock.call_args_list[index].args[1].name == name
    remote_agent = mock_agents["test.remote"]
    for backup_id, (backup, expected_backup_data) in remote_agent_backups.items():
        assert await remote_agent.async_get_backup(backup_id) == backup
        backup_data = bytearray()
        async for chunk in await remote_agent.async_download_backup(backup_id):
            backup_data += chunk
        assert backup_data == expected_backup_data
    assert unlink_mock.call_count == temp_file_unlink_call_count