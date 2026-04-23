async def test_reconfigure_migrate_restore_driver_ready_timeout(
    hass: HomeAssistant,
    client: MagicMock,
    integration: MockConfigEntry,
    restart_addon: AsyncMock,
    set_addon_options: AsyncMock,
) -> None:
    """Test migration flow with driver ready timeout after nvm restore."""
    entry = integration
    assert client.connect.call_count == 1
    assert client.driver.controller.home_id == 3245146787
    assert entry.unique_id == "3245146787"
    hass.config_entries.async_update_entry(
        entry,
        data={
            "url": "ws://localhost:3000",
            "use_addon": True,
            "usb_path": "/dev/ttyUSB0",
        },
    )

    async def mock_restart_addon(addon_slug: str) -> None:
        client.driver.controller.data["homeId"] = 1234

    restart_addon.side_effect = mock_restart_addon

    async def mock_backup_nvm_raw():
        await asyncio.sleep(0)
        client.driver.controller.emit(
            "nvm backup progress", {"bytesRead": 100, "total": 200}
        )
        return b"test_nvm_data"

    client.driver.controller.async_backup_nvm_raw = AsyncMock(
        side_effect=mock_backup_nvm_raw
    )

    async def mock_restore_nvm(data: bytes, options: dict[str, bool] | None = None):
        client.driver.controller.emit(
            "nvm convert progress",
            {"event": "nvm convert progress", "bytesRead": 100, "total": 200},
        )
        await asyncio.sleep(0)
        client.driver.controller.emit(
            "nvm restore progress",
            {"event": "nvm restore progress", "bytesWritten": 100, "total": 200},
        )
        client.driver.controller.data["homeId"] = 3245146787

    client.driver.controller.async_restore_nvm = AsyncMock(side_effect=mock_restore_nvm)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESS_UPDATE
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
        assert len(events) == 1
        assert events[0].data["progress"] == 0.5
        events.clear()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "instruct_unplug"
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_serial_port"
    data_schema = result["data_schema"]
    assert data_schema is not None
    assert data_schema.schema[CONF_USB_PATH]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USB_PATH: "/test",
        },
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"
    assert set_addon_options.call_args == call(
        "core_zwave_js", AddonsOptions(config={"device": "/test"})
    )

    await hass.async_block_till_done()

    assert restart_addon.call_args == call("core_zwave_js")

    with patch(
        ("homeassistant.components.zwave_js.helpers.DRIVER_READY_EVENT_TIMEOUT"),
        new=0,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "restore_nvm"
        assert client.connect.call_count == 2

        await hass.async_block_till_done()
        assert client.connect.call_count == 3
        assert entry.state is config_entries.ConfigEntryState.LOADED
        assert client.driver.controller.async_restore_nvm.call_count == 1
        assert len(events) == 2
        assert events[0].data["progress"] == 0.25
        assert events[1].data["progress"] == 0.75

        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "migration_successful"
    assert entry.data["url"] == "ws://host1:3001"
    assert entry.data["usb_path"] == "/test"
    assert entry.data["socket_path"] is None
    assert entry.data["use_addon"] is True
    assert "keep_old_devices" in entry.data
    assert entry.unique_id == "1234"