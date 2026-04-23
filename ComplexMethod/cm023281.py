async def test_reconfigure_migrate_start_addon_failure(
    hass: HomeAssistant,
    client: MagicMock,
    integration: MockConfigEntry,
    restart_addon: AsyncMock,
    set_addon_options: AsyncMock,
) -> None:
    """Test add-on start failure during migration."""
    restart_addon.side_effect = SupervisorError("Boom!")
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
    assert set_addon_options.call_args == call(
        "core_zwave_js", AddonsOptions(config={"device": "/test"})
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_start_failed"
    assert "keep_old_devices" not in entry.data