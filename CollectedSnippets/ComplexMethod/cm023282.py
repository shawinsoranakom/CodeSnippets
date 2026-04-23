async def test_reconfigure_migrate_restore_failure(
    hass: HomeAssistant,
    client: MagicMock,
    integration: MockConfigEntry,
    set_addon_options: AsyncMock,
) -> None:
    """Test restore failure."""
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

    client.driver.controller.async_restore_nvm = AsyncMock(
        side_effect=FailedCommand("test_error", "unknown_error")
    )

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_migrate"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "backup_nvm"

    with patch("pathlib.Path.write_bytes") as mock_file:
        await hass.async_block_till_done()
        assert client.driver.controller.async_backup_nvm_raw.call_count == 1
        assert mock_file.call_count == 1

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "instruct_unplug"
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_serial_port"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USB_PATH: "/test",
        },
    )

    assert set_addon_options.call_count == 1
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "restore_nvm"

    await hass.async_block_till_done()

    assert client.driver.controller.async_restore_nvm.call_count == 1

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "restore_failed"
    description_placeholders = result["description_placeholders"]
    assert description_placeholders is not None
    assert description_placeholders["file_path"]
    assert description_placeholders["file_url"]
    assert description_placeholders["file_name"]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "restore_nvm"

    await hass.async_block_till_done()

    assert client.driver.controller.async_restore_nvm.call_count == 2

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "restore_failed"

    hass.config_entries.flow.async_abort(result["flow_id"])

    assert len(hass.config_entries.flow.async_progress()) == 0
    assert "keep_old_devices" not in entry.data