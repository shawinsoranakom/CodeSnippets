async def test_update_addon_with_backup_removes_old_backups(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    update_addon: AsyncMock,
    ws_commands: list[dict[str, Any]],
    backups: dict[str, ManagerBackup],
    removed_backups: list[str],
) -> None:
    """Test updating addon update entity."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        assert result
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)

    for command in ws_commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        assert result["success"]

    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_create_backup",
        ) as mock_create_backup,
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_delete_backup",
            autospec=True,
            return_value={},
        ) as async_delete_backup,
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backups",
            return_value=(backups, {}),
        ),
    ):
        await client.send_json_auto_id(
            {"type": "hassio/update/addon", "addon": "test", "backup": True}
        )
        result = await client.receive_json()
        assert result["success"]
    mock_create_backup.assert_called_once_with(
        agent_ids=["hassio.local"],
        extra_metadata={"supervisor.addon_update": "test"},
        include_addons=["test"],
        include_all_addons=False,
        include_database=False,
        include_folders=None,
        include_homeassistant=False,
        name="test 2.0.0",
        password=None,
    )
    assert len(async_delete_backup.mock_calls) == len(removed_backups)
    for call in async_delete_backup.mock_calls:
        assert call.args[1] in removed_backups
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))