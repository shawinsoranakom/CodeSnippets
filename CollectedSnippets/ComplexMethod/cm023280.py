async def test_reconfigure_migrate_backup_file_failure(
    hass: HomeAssistant,
    integration: MockConfigEntry,
    client: MagicMock,
) -> None:
    """Test backup file failure."""
    entry = integration
    hass.config_entries.async_update_entry(
        entry, unique_id="1234", data={**entry.data, "use_addon": True}
    )

    async def mock_backup_nvm_raw():
        await asyncio.sleep(0)
        return b"test_nvm_data"

    client.driver.controller.async_backup_nvm_raw = AsyncMock(
        side_effect=mock_backup_nvm_raw
    )

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_migrate"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "backup_nvm"

    with patch("pathlib.Path.write_bytes", side_effect=OSError("test_error")):
        await hass.async_block_till_done()
        assert client.driver.controller.async_backup_nvm_raw.call_count == 1

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "backup_failed"
    assert "keep_old_devices" not in entry.data