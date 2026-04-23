async def test_remove_entry(
    hass: HomeAssistant,
    stop_addon: AsyncMock,
    create_backup: AsyncMock,
    uninstall_addon: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test remove the config entry."""
    # test successful remove without created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"integration_created_addon": False},
    )
    entry.add_to_hass(hass)
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    await hass.config_entries.async_remove(entry.entry_id)

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0

    # test successful remove with created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"integration_created_addon": True},
    )
    entry.add_to_hass(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    await hass.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")
    assert create_backup.call_count == 1
    assert create_backup.call_args == call(
        PartialBackupOptions(name="addon_core_zwave_js_1.0.0", addons={"core_zwave_js"})
    )
    assert uninstall_addon.call_count == 1
    assert uninstall_addon.call_args == call("core_zwave_js")
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    stop_addon.reset_mock()
    create_backup.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on stop failure
    entry.add_to_hass(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    stop_addon.side_effect = SupervisorError()

    await hass.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")
    assert create_backup.call_count == 0
    assert uninstall_addon.call_count == 0
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to stop the Z-Wave JS app" in caplog.text
    stop_addon.side_effect = None
    stop_addon.reset_mock()
    create_backup.reset_mock()
    uninstall_addon.reset_mock()

    # test create backup failure
    entry.add_to_hass(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    create_backup.side_effect = SupervisorError()

    await hass.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")
    assert create_backup.call_count == 1
    assert create_backup.call_args == call(
        PartialBackupOptions(name="addon_core_zwave_js_1.0.0", addons={"core_zwave_js"})
    )
    assert uninstall_addon.call_count == 0
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to create a backup of the Z-Wave JS app" in caplog.text
    create_backup.side_effect = None
    stop_addon.reset_mock()
    create_backup.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on uninstall failure
    entry.add_to_hass(hass)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    uninstall_addon.side_effect = SupervisorError()

    await hass.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")
    assert create_backup.call_count == 1
    assert create_backup.call_args == call(
        PartialBackupOptions(name="addon_core_zwave_js_1.0.0", addons={"core_zwave_js"})
    )
    assert uninstall_addon.call_count == 1
    assert uninstall_addon.call_args == call("core_zwave_js")
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to uninstall the Z-Wave JS app" in caplog.text